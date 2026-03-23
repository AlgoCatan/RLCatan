import time
import os
import json
from collections import defaultdict

from catanatron.explanations.packet_builder import ExplanationPacketBuilder
from catanatron.game import GameAccumulator, Game
from catanatron.json import GameEncoder
from catanatron.state_functions import (
    get_actual_victory_points,
    get_dev_cards_in_hand,
    get_largest_army,
    get_longest_road_color,
    get_player_buildings,
)
from catanatron.models.enums import (
    VICTORY_POINT,
    SETTLEMENT,
    CITY,
)


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
    Accumulates structured bot decision packets for use in explanation.

    The packet is layered:
      - decision_info: from Player, possibly extended by specific Player subclasses
      - player_summary: compact actor summary
      - board_context: broad board/race/opponent context
      - action_context: exact interpretation of the chosen move
    """

    def __init__(self, output_dir=None, recent_action_count=5, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.output_dir = output_dir
        self.recent_action_count = recent_action_count # How many recent actions to include in the explanation packet for context
        self.packets = []
        self.current_game_id = None

        self.builder = ExplanationPacketBuilder(recent_action_count=recent_action_count)

        if self.output_dir is not None:
            os.makedirs(self.output_dir, exist_ok=True)

    def before(self, game):
        # Reset for the new active game
        self.current_game_id = game.id
        self.packets = []

    def step(self, game_before_action, _):
        """Capture pre-action state and decision info before execute() mutates the game."""
        player = game_before_action.state.current_player()

        # I originally had player move explanations disabled, but we've decided that it's
        # actually more consistent to capture explanations for all decisions, not just bots.
        # If we want to filter out human player decisions later, we can do that in the analysis
        # phase instead of here in the accumulation phase.

        # if not player.is_bot:
        #     return

        snapshot = game_before_action.copy()
        decision_info = getattr(player, "last_decision_info", None)

        packet = self.builder.build_explanation_packet(snapshot, decision_info)
        self.store_for_later(packet)

    def store_for_later(self, packet):
        """Store the packet in memory and optionally write it to disk for later analysis."""
        self.packets.append(packet)

        # Adding the option to write to disk in case we want to do analysis on the packets for debugging
        if self.output_dir is not None:
            filepath = os.path.join(self.output_dir, f"{self.current_game_id}_explanations.jsonl")

            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(packet) + "\n")

    def get_packet(self, action_index):
        if action_index < 0 or action_index >= len(self.packets):
            raise IndexError(
                f"Action index {action_index} out of range. "
                f"Valid range: 0..{len(self.packets) - 1}"
            )

        return self.packets[action_index]