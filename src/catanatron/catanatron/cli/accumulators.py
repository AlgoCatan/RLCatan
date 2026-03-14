import time
import os
import json
from collections import defaultdict

from catanatron.game import GameAccumulator, Game
from catanatron.json import GameEncoder
from catanatron.models.actions import serialize_action
from catanatron.state_functions import (
    get_actual_victory_points,
    get_dev_cards_in_hand,
    get_largest_army,
    get_longest_road_color,
    get_player_buildings,
)
from catanatron.models.enums import VICTORY_POINT, SETTLEMENT, CITY


class VpDistributionAccumulator(GameAccumulator):
    """
    Accumulates CITIES,SETTLEMENTS,DEVVPS,LONGEST,LARGEST
    in each game per player.
    """

    def __init__(self):
        # These are all per-player. e.g. self.cities['RED']
        self.cities = defaultdict(int)
        self.settlements = defaultdict(int)
        self.devvps = defaultdict(int)
        self.longest = defaultdict(int)
        self.largest = defaultdict(int)

        self.num_games = 0

    def after(self, game: Game):
        winner = game.winning_color()
        if winner is None:
            return  # throw away data

        for color in game.state.colors:
            cities = len(get_player_buildings(game.state, color, CITY))
            settlements = len(get_player_buildings(game.state, color, SETTLEMENT))
            longest = get_longest_road_color(game.state) == color
            largest = get_largest_army(game.state)[0] == color
            devvps = get_dev_cards_in_hand(game.state, color, VICTORY_POINT)

            self.cities[color] += cities
            self.settlements[color] += settlements
            self.longest[color] += longest
            self.largest[color] += largest
            self.devvps[color] += devvps

        self.num_games += 1

    def get_avg_cities(self, color=None):
        if color is None:
            return sum(self.cities.values()) / self.num_games
        else:
            return self.cities[color] / self.num_games

    def get_avg_settlements(self, color=None):
        if color is None:
            return sum(self.settlements.values()) / self.num_games
        else:
            return self.settlements[color] / self.num_games

    def get_avg_longest(self, color=None):
        if color is None:
            return sum(self.longest.values()) / self.num_games
        else:
            return self.longest[color] / self.num_games

    def get_avg_largest(self, color=None):
        if color is None:
            return sum(self.largest.values()) / self.num_games
        else:
            return self.largest[color] / self.num_games

    def get_avg_devvps(self, color=None):
        if color is None:
            return sum(self.devvps.values()) / self.num_games
        else:
            return self.devvps[color] / self.num_games


class StatisticsAccumulator(GameAccumulator):
    def __init__(self):
        self.wins = defaultdict(int)
        self.turns = []
        self.ticks = []
        self.durations = []
        self.games = []
        self.results_by_player = defaultdict(list)

    def before(self, game):
        self.start = time.time()

    def after(self, game):
        duration = time.time() - self.start
        winning_color = game.winning_color()
        if winning_color is None:
            return  # do not track

        self.wins[winning_color] += 1
        self.turns.append(game.state.num_turns)
        self.ticks.append(len(game.state.actions))
        self.durations.append(duration)
        self.games.append(game)

        for color in game.state.colors:
            points = get_actual_victory_points(game.state, color)
            self.results_by_player[color].append(points)

    def get_avg_ticks(self):
        return sum(self.ticks) / len(self.ticks)

    def get_avg_turns(self):
        return sum(self.turns) / len(self.turns)

    def get_avg_duration(self):
        return sum(self.durations) / len(self.durations)


class JsonDataAccumulator(GameAccumulator):
    def __init__(self, output):
        self.output = output

    def after(self, game):
        filepath = os.path.join(self.output, f"{game.id}.json")
        with open(filepath, "w") as f:
            f.write(json.dumps(game, cls=GameEncoder))


class ExplanationAccumulator(GameAccumulator):
    """
    Accumulates structured bot decision packets for use in LLM move explanation.
    """

    def __init__(self, output_dir=None, recent_action_count=5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.output_dir = output_dir
        self.recent_action_count = recent_action_count # How many recent actions to include in the explanation packet for context
        self.packets = []
        self.packets_by_game = defaultdict(list)

        if self.output_dir is not None:
            os.makedirs(self.output_dir, exist_ok=True)

    def step(self, game_before_action, _):
        """Accumulate information about the current game state and bot decision for use in LLM move explanation."""
        snapshot = game_before_action.copy()
        player = snapshot.state.current_player()

        if not player.is_bot:
            return  # Don't want to try to explain a human player's moves back to them

        decision_info = getattr(player, "last_decision_info", None)

        packet = self.build_explanation_packet(snapshot, decision_info)
        self.store_for_later(packet)

    def build_explanation_packet(self, snapshot, decision_info):
        """Build a packet of information about the current game state and decision, for use in LLM move explanation."""
        state = snapshot.state
        actor = state.current_color()

        # I don't think is possible for decision_info to be None, but just in case some testcase
        # bypasses the new decide_with_context() flow, this will handle things gracefully.
        if decision_info is None:
            decision_info = {}

        return {
            # Basic info about the game state. Info on the action comes from the player making the decision (decision_info)
            "game_id": snapshot.id,
            "decision_index": len(state.actions),
            "recent_actions": [serialize_action(a) for a in state.actions[-self.recent_action_count:]],
            "player_summary": {
                "actual_victory_points": get_actual_victory_points(state, actor),
                "settlements": len(get_player_buildings(state, actor, SETTLEMENT)),
                "cities": len(get_player_buildings(state, actor, CITY)),
                "has_longest_road": get_longest_road_color(state) == actor,
                "has_largest_army": get_largest_army(state)[0] == actor,
                "dev_cards_in_hand": get_dev_cards_in_hand(state, actor),
            },
            **decision_info
        }

    def store_for_later(self, packet):
        """Store the packet in memory and optionally write it to disk for later analysis."""
        self.packets.append(packet)
        self.packets_by_game[packet["game_id"]].append(packet)

        # Adding the option to write to disk in case we want to do analysis on the packets for debugging
        if self.output_dir is not None:
            filepath = os.path.join(self.output_dir, f"{packet['game_id']}_explanations.jsonl")

            with open(filepath, "a") as f:
                f.write(json.dumps(packet) + "\n")