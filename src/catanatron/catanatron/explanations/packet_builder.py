from collections import Counter

from catanatron.models.actions import serialize_action
from catanatron.state_functions import (
    get_actual_victory_points,
    get_dev_cards_in_hand,
    get_largest_army,
    get_longest_road_color,
    get_player_buildings,
    get_player_freqdeck,
)
from catanatron.models.enums import (
    SETTLEMENT,
    CITY,
    ROAD,
    RESOURCES,
)
from catanatron.models.board import get_node_distances
from catanatron.models.map import number_probability
from catanatron.features import get_player_expandable_nodes, get_node_production
from catanatron.state_functions import get_visible_victory_points


class ExplanationPacketBuilder:
    """
    Builds a packet of information about the current game state and decision, for use in LLM move explanation.
     - The packet includes a player summary, board context, and action context, which are all constructed to provide
       relevant information for understanding the decision in a way that's useful for explanation.
     - The player summary includes information about the player's current position in the game, such as their
       victory points, buildings, and production.
     - The board context includes information about the overall game state, such as the visible scores of all players,
       the leader, legal actions available, and the strategic context of the board.
     - The action context includes information about the chosen action, its alternatives, and its expected impact.
     - The builder also defines some static information about action costs and expected visible VP deltas for different
       action types, which are included in the action context to help explain the strategic implications of the chosen action.
    """

    ACTION_COSTS = {
        "BUILD_ROAD": {"WOOD": 1, "BRICK": 1},
        "BUILD_SETTLEMENT": {"WOOD": 1, "BRICK": 1, "SHEEP": 1, "WHEAT": 1},
        "BUILD_CITY": {"WHEAT": 2, "ORE": 3},
        "BUY_DEVELOPMENT_CARD": {"SHEEP": 1, "WHEAT": 1, "ORE": 1},
    }

    ACTION_VISIBLE_VP_DELTA = {
        "BUILD_SETTLEMENT": 1,
        "BUILD_CITY": 1,  # City replaces settlement, so net visible VP gain is also 1
    }

    def __init__(self, recent_action_count=5):
        self.recent_action_count = recent_action_count

    def build_explanation_packet(self, snapshot, decision_info):
        """Build a packet of information about the current game state and decision, for use in LLM move explanation."""
        state = snapshot.state
        actor = state.current_color()

        # I don't think is possible for decision_info to be None, but just in case some testcase
        # bypasses the new decide_with_context() flow, this will handle things gracefully.
        if decision_info is None:
            decision_info = {}

        player_summary = self._build_player_summary(state, actor)
        board_context = self._build_board_context(
            snapshot, decision_info, player_summary
        )
        action_context = self._build_action_context(
            snapshot, decision_info, player_summary, board_context
        )

        return {
            # Basic info about the game state. Info on the action comes from the player making the decision (decision_info)
            "game_id": snapshot.id,
            "decision_index": len(state.actions),
            "recent_actions": [
                serialize_action(a) for a in state.actions[-self.recent_action_count :]
            ],
            # Expanded context constructed above
            "player_summary": player_summary,
            "board_context": board_context,
            "action_context": action_context,
            # Any additional info provided by the specific Player subclass about the decision
            **decision_info,
        }

    def _build_player_summary(self, state, actor):
        """Build a compact summary of the player's current position in the game, for use in explanation."""
        settlements = sorted(get_player_buildings(state, actor, SETTLEMENT))
        cities = sorted(get_player_buildings(state, actor, CITY))
        roads = sorted(
            tuple(sorted(edge)) for edge in get_player_buildings(state, actor, ROAD)
        )

        total_prod, effective_prod = self._get_player_production(state, actor)

        # Current resource cards
        freqdeck = get_player_freqdeck(state, actor)
        resource_hand = {
            resource: count for resource, count in zip(RESOURCES, freqdeck)
        }

        owned_ports = sorted(
            {
                port
                for node_id in settlements + cities
                for port in [self._get_port_at_node(state.board.map, node_id)]
                if port is not None
            }
        )

        return {
            "actual_victory_points": get_actual_victory_points(state, actor),
            "settlements": len(settlements),
            "cities": len(cities),
            "roads": len(roads),
            "settlement_nodes": settlements,
            "city_nodes": cities,
            "road_edges": roads,
            "resource_hand": resource_hand,
            "owned_ports": owned_ports,
            "has_longest_road": get_longest_road_color(state) == actor,
            "has_largest_army": get_largest_army(state)[0] == actor,
            "dev_cards_in_hand": get_dev_cards_in_hand(state, actor),
            "total_production_by_resource": total_prod,
            "effective_production_by_resource": effective_prod,
        }

    def _build_board_context(self, snapshot, decision_info, player_summary):
        """Build a summary of the current board state and player's position relative to opponents, for use in explanation."""
        state = snapshot.state
        actor = state.current_color()

        # Don't want to leak hidden vps in the board context, so using visible rather than actual vp.
        known_scores = {
            color.value: get_visible_victory_points(state, color)
            for color in state.colors
        }
        # Override acting player's score with the accurate one from the player summary (since they know their own hidden vps)
        known_scores[actor.value] = player_summary["actual_victory_points"]

        actor_score = known_scores[actor.value]
        leader_color, leader_score = max(known_scores.items(), key=lambda x: x[1])

        buildable_nodes = list(state.board.buildable_node_ids(actor))
        buildable_node_summaries = [
            self._summarize_node(snapshot, node_id, actor)
            for node_id in buildable_nodes
        ]
        buildable_node_summaries.sort(
            key=lambda x: (x["pip_total"], x["total_production"]), reverse=True
        )

        robber_tile = state.board.map.tiles[state.board.robber_coordinate]
        robber_tile_summary = self._summarize_tile(state, robber_tile)
        robber_affected_buildings = self._buildings_touching_tile(state, robber_tile)

        opponents = []

        for color in state.colors:
            if color == actor:
                continue

            opp_summary = self._build_player_summary(state, color)
            opp_summary.pop(
                "actual_victory_points", None
            )  # Don't include opponents' hidden VP in the summary
            opp_summary["visible_victory_points"] = known_scores[color.value]
            opponents.append(opp_summary)

        return {
            "visible_scores": known_scores,
            "leader_color": leader_color,
            "leader_visible_vp": leader_score,
            "actor_visible_vp_gap_to_leader": leader_score - actor_score,
            "opponents": opponents,
            "actor_expandable_nodes_count": len(
                get_player_expandable_nodes(snapshot, actor)
            ),
            "actor_buildable_nodes_count": len(buildable_nodes),
            "actor_best_buildable_nodes": buildable_node_summaries[
                :5
            ],  # limited to top 5 for brevity
            "actor_port_distances": self._get_player_port_distances(snapshot, actor),
            "robber_tile": robber_tile_summary,
            "robber_affected_buildings": robber_affected_buildings,
        }

    def _build_action_context(
        self, snapshot, decision_info, player_summary, board_context
    ):
        """Build a detailed interpretation of the chosen action, its alternatives, and its expected impact, for use in explanation."""
        state = snapshot.state
        actor = state.current_color()

        chosen_action = decision_info.get("chosen_action", {})
        playable_actions = decision_info.get("playable_actions", [])

        action_type = chosen_action.get("action_type")
        action_value = chosen_action.get("value")

        action_type_counts = Counter(
            action.get("action_type")
            for action in playable_actions
            if action.get("action_type") is not None
        )

        # In situations such as having multiple positions to build a settlement, it's nice to see what alternative relevant actions there were
        same_type_options = [
            action
            for action in playable_actions
            if action.get("action_type") == action_type
        ]

        alternative_same_type_values = [
            action.get("value")
            for action in same_type_options
            if action != chosen_action
        ]

        context = {
            "action_type": action_type,
            "action_value": action_value,
            "legal_action_type_counts": dict(action_type_counts),
            "num_legal_actions": len(playable_actions),
            "same_type_option_count": len(same_type_options),
            "alternative_same_type_values": alternative_same_type_values[
                :8
            ],  # limited to 8 alternatives for brevity
            "is_only_action_of_this_type": len(same_type_options) == 1,
            "is_only_legal_action": len(playable_actions) == 1,
            "expected_visible_vp_delta": self.ACTION_VISIBLE_VP_DELTA.get(
                action_type, 0
            ),
            "action_cost": self.ACTION_COSTS.get(action_type, {}),
        }

        if action_type in {"BUILD_SETTLEMENT", "BUILD_CITY"}:
            target_node = action_value

            node_summary = self._summarize_node(snapshot, target_node, actor)

            blocked_opponents = (
                [  # Other players who could have built here but now can't
                    color.value
                    for color in state.colors
                    if color != actor
                    and action_value in state.board.buildable_node_ids(color)
                ]
            )

            context.update(
                {
                    "target_node_id": target_node,
                    "target_node_summary": node_summary,
                    "blocked_opponents": blocked_opponents,
                    "production_gain_by_resource": node_summary[
                        "production_by_resource"
                    ],
                    "production_gain_total": node_summary["total_production"],
                }
            )

        elif action_type == "BUILD_ROAD":
            edge = tuple(sorted(action_value))  # Normalize edge representation

            endpoint_summaries = [
                self._summarize_node(snapshot, node_id, actor) for node_id in edge
            ]
            buildable_now = set(state.board.buildable_node_ids(actor))

            # How valuable are the buildable nodes near this road, and therefore how much does this road support expansion towards valuable locations?
            nearby_buildable = []
            distances = get_node_distances()

            for node_id in buildable_now:
                dist = min(distances[edge[0]][node_id], distances[edge[1]][node_id])
                node_summary = self._summarize_node(snapshot, node_id, actor)
                node_summary["distance_from_edge"] = dist
                nearby_buildable.append(node_summary)

            nearby_buildable.sort(
                key=lambda x: (
                    x["distance_from_edge"],
                    -x["pip_total"],
                    -x["total_production"],
                )
            )

            actor_network_nodes = set()
            for component in state.board.connected_components[actor]:
                actor_network_nodes.update(component)

            context.update(
                {
                    "target_edge": edge,
                    "endpoint_nodes": list(edge),
                    "endpoint_summaries": endpoint_summaries,
                    "nearby_buildable_count": len(nearby_buildable),
                    "nearby_buildable_nodes": nearby_buildable[
                        :5
                    ],  # limited to top 5 for brevity
                    "connected_to_actor_network": any(
                        node_id in actor_network_nodes for node_id in edge
                    ),
                }
            )

        elif action_type == "MOVE_ROBBER":
            target_coordinate = None
            target_player = None
            stolen_resource = None

            # The value for MOVE_ROBBER is (target_coordinate, target_player_color, stolen_resource), but the last two are optional
            if isinstance(action_value, (list, tuple)):
                if len(action_value) > 0:
                    target_coordinate = action_value[0]
                if len(action_value) > 1:
                    target_player = action_value[1]
                if len(action_value) > 2:
                    stolen_resource = action_value[2]

            if target_coordinate is not None:
                target_coordinate = tuple(target_coordinate)

                target_tile = state.board.map.tiles[target_coordinate]
                tile_summary = self._summarize_tile(state, target_tile)
                affected_buildings = self._buildings_touching_tile(state, target_tile)

                leader_color = board_context["leader_color"]
                blocks_leader = any(
                    building["color"] == leader_color for building in affected_buildings
                )

                context.update(
                    {
                        "target_tile_coordinate": target_coordinate,
                        "target_tile_summary": tile_summary,
                        "affected_buildings": affected_buildings,
                        "blocks_leader": blocks_leader,
                        "target_player": (
                            target_player.value
                            if hasattr(target_player, "value")
                            else target_player
                        ),
                        "stolen_resource": (
                            stolen_resource.value
                            if hasattr(stolen_resource, "value")
                            else stolen_resource
                        ),
                    }
                )

        elif action_type == "DISCARD":
            # As far as I'm aware this is random right now, but if that changes we can uncomment it
            # context["discard_payload"] = action_value
            pass

        elif action_type == "BUY_DEVELOPMENT_CARD":
            # Leaving this here in case there's some info to be gained from this, but since we don't know what dev card we bought until we have it it doesn't seem too useful.
            pass

        elif action_type == "END_TURN":
            non_end_turn_actions = [
                action
                for action in playable_actions
                if action.get("action_type") != "END_TURN"
            ]

            context.update(
                {
                    "had_other_options": len(non_end_turn_actions) > 0,
                    "other_options": non_end_turn_actions[
                        :8
                    ],  # limited to 8 for brevity
                }
            )

        return context

    # Helpers
    def _get_player_production(self, state, color):
        """Calculate the player's total and effective production by resource, taking into account the robber's position."""
        board = state.board

        def production_dict(robber_coordinate=None):
            return {
                resource: sum(
                    get_node_production(board.map, node_id, resource, robber_coordinate)
                    for node_id in get_player_buildings(state, color, SETTLEMENT)
                )
                + sum(
                    2
                    * get_node_production(
                        board.map, node_id, resource, robber_coordinate
                    )
                    for node_id in get_player_buildings(state, color, CITY)
                )
                for resource in RESOURCES
            }

        total_dict = production_dict()
        effective_dict = production_dict(robber_coordinate=board.robber_coordinate)

        return total_dict, effective_dict

    def _summarize_tile(self, state, tile):
        """Build a summary of the tile's key characteristics and strategic context, for use in explanation."""
        return {
            "tile_id": tile.id,
            "resource": "DESERT" if tile.resource is None else tile.resource,
            "number": None if tile.resource is None else tile.number,
            "probability": (
                0 if tile.resource is None else number_probability(tile.number)
            ),
            "has_robber": state.board.map.tiles[state.board.robber_coordinate] == tile,
        }

    def _summarize_node(self, snapshot, node_id, actor):
        """Build a summary of the node's key characteristics and strategic context, for use in explanation."""
        state = snapshot.state
        board_map = state.board.map

        adjacent_tiles = [
            self._summarize_tile(state, tile)
            for tile in board_map.adjacent_tiles[node_id]
        ]
        production_counter = Counter(board_map.node_production[node_id])

        production_by_resource = {
            resource: production_counter.get(resource, 0) for resource in RESOURCES
        }

        total_production = sum(production_by_resource.values())
        pip_total = sum(tile["probability"] for tile in adjacent_tiles)

        port = self._get_port_at_node(board_map, node_id)
        nearest_ports = self._get_node_port_distances(board_map, node_id)

        building = state.board.buildings.get(node_id)

        occupied_by = None
        if building is not None:
            occupied_by = {
                "color": (
                    building[0].value
                    if hasattr(building[0], "value")
                    else str(building[0])
                ),
                "building_type": building[1],
            }

        return {
            "node_id": node_id,
            "adjacent_tiles": adjacent_tiles,
            "production_by_resource": production_by_resource,
            "total_production": total_production,
            "pip_total": pip_total,
            "port_at_node": port,
            "nearest_ports": nearest_ports,
            "is_buildable_for_actor": node_id in state.board.buildable_node_ids(actor),
            "occupied_by": occupied_by,
        }

    def _buildings_touching_tile(self, state, tile):
        """Return a summary of the buildings adjacent to the tile, including who occupies them and what type they are."""
        result = []
        for node_id in tile.nodes.values():
            building = state.board.buildings.get(node_id)

            if building is None:
                continue

            color, building_type = building

            result.append(
                {
                    "color": color.value if hasattr(color, "value") else str(color),
                    "node_id": node_id,
                    "building_type": building_type,
                }
            )

        return result

    def _get_port_at_node(self, board_map, node_id):
        """Check if there's a port at the given node, and if so return the type of the port."""
        for resource_or_none, port_nodes in board_map.port_nodes.items():
            if node_id in port_nodes:
                return "3:1" if resource_or_none is None else resource_or_none

        return None

    def _get_node_port_distances(self, board_map, node_id):
        """Calculate the distance from the given node to each port type, for use in explanation."""
        distances = get_node_distances()
        port_distances = {}

        resources_and_none = list(RESOURCES) + [None]
        for resource_or_none in resources_and_none:
            port_name = "3:1" if resource_or_none is None else resource_or_none
            port_nodes = board_map.port_nodes[resource_or_none]

            if not port_nodes:
                port_distances[port_name] = None

            else:
                port_distances[port_name] = min(
                    distances[node_id][port_node] for port_node in port_nodes
                )

        return port_distances

    def _get_player_port_distances(self, snapshot, color):
        """Calculate the distance from each of the player's expandable nodes to each port type, for use in explanation."""
        state = snapshot.state
        expandable_node_ids = get_player_expandable_nodes(snapshot, color)
        distances = get_node_distances()
        ports = state.board.map.port_nodes

        result = {}

        resources_and_none = list(RESOURCES) + [None]
        for resource_or_none in resources_and_none:
            port_name = "3:1" if resource_or_none is None else resource_or_none

            if len(expandable_node_ids) == 0:
                result[port_name] = None

            else:
                result[port_name] = min(
                    distances[port_node_id][my_node]
                    for my_node in expandable_node_ids
                    for port_node_id in ports[resource_or_none]
                )

        return result
