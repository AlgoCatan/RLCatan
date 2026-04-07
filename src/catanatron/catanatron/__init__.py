"""
Module: 9. Game State Manager
Author: Forked
Date: 2026-02-07
Purpose: Implements the package initializer module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

"""
This is to allow an API like:

from catanatron import Game, Player, Color, Accumulator
"""

from catanatron.game import Game, GameAccumulator
from catanatron.models.player import Player, Color, RandomPlayer
from catanatron.models.enums import (
    Action,
    ActionType,
    WOOD,
    BRICK,
    SHEEP,
    WHEAT,
    ORE,
    RESOURCES,
)
