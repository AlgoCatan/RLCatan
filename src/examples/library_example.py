"""
Module: 9. Game State Manager
Author: Forked
Date: 2025-11-15
Purpose: Implements the library example module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

from catanatron import Game, RandomPlayer, Color

# Play a simple 4v4 game
players = [
    RandomPlayer(Color.RED),
    RandomPlayer(Color.BLUE),
    RandomPlayer(Color.WHITE),
    RandomPlayer(Color.ORANGE),
]
game = Game(players)
print(game.play())  # returns winning color
