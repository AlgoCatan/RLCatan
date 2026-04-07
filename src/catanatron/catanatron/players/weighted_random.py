"""
Module: 3. AI Model
Author: Forked
Date: 2025-12-03
Purpose: Implements the weighted random module for the AI model component, supporting automated decision-making or search-based gameplay behavior.
"""

import random

from catanatron.models.player import Player
from catanatron.models.actions import ActionType

WEIGHTS_BY_ACTION_TYPE = {
    ActionType.BUILD_CITY: 10000,
    ActionType.BUILD_SETTLEMENT: 1000,
    ActionType.BUY_DEVELOPMENT_CARD: 100,
}


class WeightedRandomPlayer(Player):
    """
    Player that decides at random, but skews distribution
    to actions that are likely better (cities > settlements > dev cards).
    """

    def decide(self, game, playable_actions):
        bloated_actions = []
        for action in playable_actions:
            weight = WEIGHTS_BY_ACTION_TYPE.get(action.action_type, 1)
            bloated_actions.extend([action] * weight)

        return random.choice(bloated_actions)
