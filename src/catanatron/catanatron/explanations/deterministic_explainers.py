from __future__ import annotations
from typing import Any


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    """Basic set-based dedupe that preserves order"""
    seen = set()
    deduped = []

    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped


def _format_num(value: Any, digits: int = 3) -> str:
    """Format a number to a string with a specified number of decimal places, removing trailing zeros."""
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def _format_resource_mix(prod_dict: dict[str, int] | None) -> str:
    """
    Formats a resource production dictionary into a human-readable string.
    Ex. {"WOOD": 2, "BRICK": 1, "SHEEP": 0, "WHEAT": 3, "ORE": 0} -> "wood (2), brick (1), wheat (3)"
    """
    if not prod_dict:
        return "none"

    nonzero = [(k, v) for k, v in prod_dict.items() if v]

    if not nonzero:
        return "none"

    return ", ".join(f"{resource} ({_format_num(value)})" for resource, value in nonzero)


def _format_tile(tile: dict[str, Any]) -> str:
    """
    Formats a tile dictionary into a human-readable string.
    """

    resource = tile.get("resource")
    number = tile.get("number")
    probability = tile.get("probability")

    if resource == "DESERT":
        return "desert"

    return f"{str(resource).lower()} on {number} (pip weight {_format_num(probability)})"


def _format_tile_list(adjacent_tiles: list[dict[str, Any]] | None) -> str:
    """Formats a list of tile dictionaries into a human-readable string."""
    if not adjacent_tiles:
        return "no adjacent tiles"

    return ", ".join(_format_tile(tile) for tile in adjacent_tiles)


def _format_port_distances(port_distances: dict[str, int | None] | None) -> str:
    """
    Formats a port distance dictionary into a human-readable string, showing the three closest ports and their distances.
    Ex. {"3:1": 2, "2:1_WOOD": 1} -> "2:1 wood (1), 3:1 (2)"
    """
    if not port_distances:
        return "unknown"

    ranked = [(port, dist) for port, dist in port_distances.items() if dist is not None]

    if not ranked:
        return "no reachable ports"

    ranked.sort(key=lambda port: port[1])

    return ", ".join(f"{port} ({dist})" for port, dist in ranked[:3])


def _format_building_list(buildings: list[dict[str, Any]] | None) -> str:
    """
    Formats a list of building dictionaries into a human-readable string.
    Ex. [{"building_type": "SETTLEMENT", "color": "RED", "node_id": 5}] -> "red settlement at node 5"
    """

    if not buildings:
        return "no adjacent buildings"

    parts = []

    for building in buildings:
        parts.append(
            f"{building.get('color')} {str(building.get('building_type')).lower()} at node {building.get('node_id')}"
        )

    return ", ".join(parts)


def _count_by_color(buildings: list[dict[str, Any]] | None) -> dict[str, int]:
    """Counts the number of buildings of each color in a list of building dictionaries."""
    counts: dict[str, int] = {}

    if not buildings:
        return counts

    for building in buildings:
        color = building.get("color")

        if color is not None:
            counts[color] = counts.get(color, 0) + 1

    return counts


def extract_common_facts(packet: dict) -> dict:
    """
    Pull out a small normalized fact bundle from the richer packet.
    The packet remains the source of truth. This just avoids repeated lookups.
    """
    chosen = packet["chosen_action"]
    playable = packet.get("playable_actions", [])
    player_summary = packet.get("player_summary", {})
    board_context = packet.get("board_context", {})
    action_context = packet.get("action_context", {})

    all_valid_indices = packet.get("all_valid_indices")
    filtered_indices = packet.get("filtered_indices")

    return {
        "bot_class": packet.get("bot_class"),
        "prompt": packet.get("prompt"),
        "chosen_type": chosen.get("action_type"),
        "chosen_value": chosen.get("value"),
        "num_legal_actions": len(playable),
        "is_forced": len(playable) == 1,

        "actual_vp": player_summary.get("actual_victory_points"),
        "settlements": player_summary.get("settlements"),
        "cities": player_summary.get("cities"),
        "roads": player_summary.get("roads"),
        "resource_hand": player_summary.get("resource_hand"),
        "owned_ports": player_summary.get("owned_ports"),
        "has_longest_road": player_summary.get("has_longest_road"),
        "has_largest_army": player_summary.get("has_largest_army"),
        "dev_cards_in_hand": player_summary.get("dev_cards_in_hand"),
        "total_prod": player_summary.get("total_production_by_resource", {}),
        "effective_prod": player_summary.get("effective_production_by_resource", {}),

        "leader_color": board_context.get("leader_color"),
        "leader_visible_vp": board_context.get("leader_visible_vp"),
        "vp_gap_to_leader": board_context.get("actor_visible_vp_gap_to_leader"),
        "visible_scores": board_context.get("visible_scores", {}),
        "port_distances": board_context.get("actor_port_distances", {}),
        "expandable_nodes_count": board_context.get("actor_expandable_nodes_count"),
        "buildable_nodes_count": board_context.get("actor_buildable_nodes_count"),
        "best_buildable_nodes": board_context.get("actor_best_buildable_nodes", []),
        "robber_tile": board_context.get("robber_tile"),
        "robber_affected_buildings": board_context.get("robber_affected_buildings", []),
        "opponents": board_context.get("opponents", []),

        "action_type": action_context.get("action_type"),
        "action_value": action_context.get("action_value"),
        "only_action_of_type": action_context.get("is_only_action_of_this_type"),
        "same_type_option_count": action_context.get("same_type_option_count"),
        "alternatives_of_same_type": action_context.get("alternative_same_type_values", []),
        "alternative_same_type_values": action_context.get("alternative_same_type_values", []),
        "legal_action_type_counts": action_context.get("legal_action_type_counts", {}),
        "num_same_type_options": action_context.get("same_type_option_count"),
        "expected_visible_vp_delta": action_context.get("expected_visible_vp_delta"),
        "action_cost": action_context.get("action_cost"),

        # Unique to settlement or city building actions
        "target_node_summary": action_context.get("target_node_summary", {}),
        "blocked_opponents": action_context.get("blocked_opponents", []),
        "production_gain_by_resource": action_context.get("production_gain_by_resource"),

        # Unique to road building actions
        "target_edge": action_context.get("target_edge"),
        "endpoint_summaries": action_context.get("endpoint_summaries", []),
        "nearby_buildable_count": action_context.get("nearby_buildable_count"),
        "nearby_buildable_nodes": action_context.get("nearby_buildable_nodes", []),

        # Unique to robber moving actions
        "target_tile_summary": action_context.get("target_tile_summary"),
        "target_player": action_context.get("target_player"),
        #"stolen_resource": action_context.get("stolen_resource"), Currently random so not useful
        "affected_buildings": action_context.get("affected_buildings", []),
        "blocks_leader": action_context.get("blocks_leader"),

        # Unique to end turn actions
        "had_other_options": action_context.get("had_other_options"),
        "other_options": action_context.get("other_options", []),

        # Data specific to the PPO bot. Won't be included for other bots.
        "ppo_all_valid_indices": all_valid_indices,
        "ppo_filtered_indices": filtered_indices,
        "ppo_chosen_index": packet.get("chosen_index"),
        "ppo_deterministic": packet.get("deterministic"),
        "obs": packet.get("obs"),
    }


def explain_common(facts: dict[str, Any]) -> list[str]:
    """Explains the bot's decision based on common facts about the game state that apply to certain situations."""

    reasons: list[str] = []

    if facts["is_forced"]:
        reasons.append("This was the only legal action available.")

    prompt = facts["prompt"]
    action_type = facts["chosen_type"]

    if prompt == "BUILD_INITIAL_SETTLEMENT":
        reasons.append("This was an opening placement decision, so early board position and future resource access matter most.")
    elif prompt == "BUILD_INITIAL_ROAD":
        reasons.append("This was an opening road placement, so the move mainly affects future expansion paths.")
    elif prompt == "PLAY_TURN":
        reasons.append("This was a normal turn decision, so the bot was choosing among its currently legal tactical options.")
    elif prompt == "MOVE_ROBBER":
        reasons.append("This was a robber decision, so disruption and denial are likely important.")
    elif prompt == "DISCARD":
        reasons.append("This was a discard decision, so the main concern is minimizing lost value while keeping future options open.")
    elif prompt == "DECIDE_TRADE":
        reasons.append("This was a trade decision, so the bot was weighing short-term conversion against future flexibility.")
    elif prompt == "DECIDE_ACCEPTEES":
        reasons.append("This was a response to a proposed trade, so the bot was weighing whether the exchange improved its position.")

    if action_type == "BUILD_CITY":
        reasons.append("Upgrading to a city usually strengthens resource production at an already valuable location.")
    elif action_type == "BUILD_SETTLEMENT":
        reasons.append("Building a settlement usually improves expansion, resource access, and victory point progress.")
    elif action_type == "BUILD_ROAD":
        reasons.append("Building a road usually supports expansion, connectivity, or longest road pressure.")
    elif action_type == "BUY_DEVELOPMENT_CARD":
        reasons.append("Buying a development card usually means the bot preferred hidden value or future tactical flexibility over an immediate board commitment.")
    elif action_type == "MOVE_ROBBER":
        reasons.append("Moving the robber usually disrupts an opponent's resource production and may yield a card steal.")
    elif action_type == "END_TURN":
        reasons.append("Ending the turn suggests the bot judged that no available action was worth taking immediately.")

    actual_vp = facts["actual_vp"]
    if actual_vp is not None:
        reasons.append(f"The bot had {actual_vp} victory points.")

        if actual_vp >= 8:
            reasons.append("The bot was close to winning, so it likely prioritized high-impact actions that could secure victory.")
        elif actual_vp <= 2:
            reasons.append("This is still an early position, so building future production and expansion tends to matter more.")
        else:
            reasons.append("This looks like a mid-game position, where the bot likely balanced development with immediate tactical gains.")

    resource_hand = facts["resource_hand"]
    if resource_hand:
        hand_size = sum(resource_hand.values())

        if hand_size == 0:
            reasons.append("The bot had no resource cards this turn")
        else:
            reasons.append(f"The bot had the following resource hand: {resource_hand}")

        if hand_size >= 7:
            reasons.append("The bot had 7 or more cards, so it may have been trying to avoid losing half of them to the robber.")

    return reasons


def explain_board_context(facts: dict[str, Any]) -> list[str]:
    """Explains the bot's decision based on the broader board context."""
    reasons: list[str] = []

    visible_scores = facts["visible_scores"]

    if visible_scores:
        reasons.append(f"Known score race: {visible_scores}.")

    leader_gap = facts["vp_gap_to_leader"]
    leader_color = facts["leader_color"]

    if leader_gap is not None:
        if leader_gap == 0:
            reasons.append("The bot was currently in the lead (or tied), so it may have prioritized solidifying its position and securing victory.")
        else:
            reasons.append(f"The bot was {leader_gap} point(s) behind the current known leader ({leader_color}).")

    total_prod = facts["total_prod"]
    effective_prod = facts["effective_prod"]
    if total_prod:
        reasons.append(f"Total production profile: {_format_resource_mix(total_prod)}.")
    if effective_prod and effective_prod != total_prod:
        reasons.append(f"Effective production after robber impact: {_format_resource_mix(effective_prod)}.")

    if facts["has_longest_road"]:
        reasons.append("The bot currently holds Longest Road.")
    if facts["has_largest_army"]:
        reasons.append("The bot currently holds Largest Army.")

    dev_cards = facts["dev_cards_in_hand"]
    if dev_cards:
        reasons.append(f"The bot has {dev_cards} development card(s) in hand.")

    owned_ports = facts["owned_ports"]
    if owned_ports:
        reasons.append(f"The bot has the following ports: {owned_ports}")
    else:
        reasons.append(f"The bot has no ports.")

    port_distances = facts["port_distances"]
    if port_distances:
        reasons.append(f"Nearest ports from the bot's expandable network are {_format_port_distances(port_distances)}.")

    expandable_count = facts["expandable_nodes_count"]
    if expandable_count is not None:
        reasons.append(f"The bot currently has {expandable_count} expandable node(s) reachable from their network.")

    buildable_count = facts["buildable_nodes_count"]
    if buildable_count is not None:
        reasons.append(f"There are {buildable_count} currently legal node(s) where the bot could build a settlement.")

    best_nodes = facts["best_buildable_nodes"]
    if best_nodes:
        best = best_nodes[0]
        reasons.append(
            f"One strong current settlement candidate is node {best['node_id']}, touching {_format_tile_list(best['adjacent_tiles'])},"
            f" with pip total {_format_num(best['pip_total'])} and production {_format_resource_mix(best['production_by_resource'])}."
        )

    robber_tile = facts["robber_tile"]
    robber_affected = facts["robber_affected_buildings"]
    if robber_tile:
        reasons.append(f"The robber is currently on {_format_tile(robber_tile)}.")

        if robber_affected:
            affected_counts = _count_by_color(robber_affected)
            reasons.append(f"The current robber placement is affecting adjacent buildings from {affected_counts}.")

    legal_action_type_counts = facts["legal_action_type_counts"]
    if legal_action_type_counts:
        reasons.append(f"Legal action mix this turn: {legal_action_type_counts}.")

    opponents = facts["opponents"]
    if opponents:
        sorted_opponents = sorted(
            opponents,
            key=lambda opp: opp.get("visible_victory_points", 0),
            reverse=True,
        )
        top_opp = sorted_opponents[0]
        reasons.append(
            f"The strongest visible opponent is at {top_opp.get('visible_victory_points', 0)} points with production {_format_resource_mix(top_opp.get('effective_production_by_resource', {}))}."
        )

    return reasons


def explain_action_context(facts: dict[str, Any]) -> list[str]:
    """Explains the bot's decision based on the specific tactical context of the chosen action."""
    reasons: list[str] = []

    action_type = facts["action_type"]
    if action_type is None:
        return reasons

    if facts["only_action_of_type"]:
        reasons.append(f"This was the only legal action of type {action_type.lower()} available.")
    else:
        same_type_count = facts["same_type_option_count"]
        if same_type_count is not None:
            reasons.append(f"There were {same_type_count} legal action(s) of this same action type available")

        alternatives = facts["alternative_same_type_values"]
        if alternatives:
            reasons.append(f"Other legal actions of the same type had values {alternatives}.")

    expected_vp_delta = facts["expected_visible_vp_delta"]
    if expected_vp_delta:
        reasons.append(f"This move is expected to change visible victory points by {expected_vp_delta} immediately.")

    action_cost = facts["action_cost"]
    if action_cost:
        reasons.append(f"This action has a resource cost of {action_cost}.")

    if action_type in {"BUILD_SETTLEMENT", "BUILD_CITY"}:
        node_summary = facts["target_node_summary"]

        if node_summary:
            reasons.append(
                f"The target node {node_summary['node_id']} touches {_format_tile_list(node_summary['adjacent_tiles'])}, "
                f"with pip total {node_summary['pip_total']} and production {_format_resource_mix(node_summary['production_by_resource'])}."
            )

            if node_summary.get("port_at_node") is not None:
                reasons.append(f"This node is on a {node_summary['port_at_node']} port.")
            else:
                reasons.append(f"Nearest ports from that node are {_format_port_distances(node_summary['nearest_ports'])}.")

        blocked_opponents = facts["blocked_opponents"]
        if blocked_opponents:
            reasons.append(f"Building here blocks opponent(s) {blocked_opponents} from expanding to this node.")

        gain = facts["production_gain_by_resource"]
        if gain:
            if action_type == "BUILD_CITY":
                reasons.append(f"This city upgrade adds production roughly equivalent to {_format_resource_mix(gain)}.")
            else:
                reasons.append(f"This settlement adds production roughly equivalent to {_format_resource_mix(gain)}.")

    elif action_type == "BUILD_ROAD":
        endpoint_summaries = facts["endpoint_summaries"]
        if endpoint_summaries:
            endpoint_text = []

            for summary in endpoint_summaries:
                endpoint_text.append(f"node {summary['node_id']} ({_format_tile_list(summary['adjacent_tiles'])})")

            reasons.append(f"The road connects endpoints " + "; ".join(endpoint_text) + ".")

        nearby_count = facts["nearby_buildable_count"]
        if nearby_count is not None:
            reasons.append(f"There are {nearby_count} buildable settlement nodes near this road.")

        nearby_nodes = facts["nearby_buildable_nodes"]
        if nearby_nodes:
            best = nearby_nodes[0]
            reasons.append(
                f"The strongest nearby settlement target appears to be node {best['node_id']} at distance {best['distance_from_edge']}, touching {_format_tile_list(best['adjacent_tiles'])}."
            )

    elif action_type == "MOVE_ROBBER":
        tile_summary = facts["target_tile_summary"]
        if tile_summary:
            reasons.append(f"The robber was moved to {_format_tile(tile_summary)}.")

        affected = facts["affected_buildings"]
        if affected:
            affected_counts = _count_by_color(affected)
            reasons.append(f"This move affects adjacent buildings from {affected_counts}.")

        if facts["blocks_leader"]:
            reasons.append("This robber move also blocks the current leader, so it may have been intended to disrupt their production")

        target_player = facts["target_player"]
        if target_player is not None:
            reasons.append(f"The selected steal target was {target_player}.")

    elif action_type == "END_TURN":
        if facts["had_other_options"]:
            reasons.append("The bot ended the turn despite having other available moves.")
        else:
            reasons.append("There were no other non-END_TURN actions available.")

        other_options = facts["other_options"]
        if other_options:
            other_types = sorted(
                {option.get("action_type") for option in other_options if option.get("action_type")}
            )
            reasons.append(f"Other available action types included: {other_types}.")

    return reasons


def explain_bot_specific(facts: dict[str, Any]) -> list[str]:
    """Explains the bot's decision based on its specific class and any additional metadata it provided about the decision."""
    reasons: list[str] = []
    bot_class = facts["bot_class"]

    # Don't have these for every bot yet, although it would be nice to have that implemented in the future
    if bot_class == "SimplePlayer":
        reasons.append("This bot follows a simple rule-based policy and picks the first legal action in the list.")
    elif bot_class == "RandomPlayer":
        reasons.append("This bot chooses randomly from the legal actions, so the move is not based on strategic evaluation.")
    elif bot_class == "HumanPlayer":
        reasons.append(
            "This actually wasn't a bot, it was a human player. As such, avoid bot related terminology and"
            "emphasize that this is just a prediction of why the player made that move.")
    elif bot_class == "PPOPlayer":
        reasons.append("This bot uses a PPO policy, which evaluates the encoded game state and chooses among valid masked actions.")

        deterministic = facts["ppo_deterministic"]
        if deterministic:
            reasons.append("The PPO policy was queried in deterministic mode, so it selected its highest-preference legal action rather than sampling.")
        else:
            reasons.append("The PPO policy was queried in stochastic mode, so some randomness may have influenced the final choice.")

        chosen_index = facts["ppo_chosen_index"]
        if chosen_index is not None:
            reasons.append(f"The chosen action corresponded to policy action index {chosen_index}.")

        all_valid_indices = facts["ppo_all_valid_indices"]
        if all_valid_indices is not None:
            reasons.append(f"There were {len(all_valid_indices)} valid action-space indices before filtering.")

        filtered_indices = facts["ppo_filtered_indices"]
        if filtered_indices is not None:
            reasons.append(f"{len(filtered_indices)} legal policy actions remained after action filtering.")

        obs = facts["obs"]
        if obs is not None:
            reasons.append(f"The PPO policy received an observation vector of length {len(obs)} representing the game state.")

    return reasons


def explain_packet(packet: dict) -> dict:
    """Generate a deterministic explanation for a bot decision based on the information in the packet."""
    facts = extract_common_facts(packet)

    explanation: list[str] = []
    explanation.extend(explain_common(facts))
    explanation.extend(explain_board_context(facts))
    explanation.extend(explain_action_context(facts))
    explanation.extend(explain_bot_specific(facts))
    explanation = _dedupe_preserve_order(explanation)

    confidence_basis = "generic"

    if packet.get("bot_class") in {"SimplePlayer", "RandomPlayer"}:
        confidence_basis = "rule-based"

    if packet.get("chosen_index") is not None or packet.get("filtered_indices") is not None:
        confidence_basis = "policy-metadata"

    return {
        "explanation": explanation,
        "reasoning_mode": "deterministic",
        "confidence_basis": confidence_basis,
        "facts_used": facts,
    }