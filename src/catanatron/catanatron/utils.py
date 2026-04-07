"""
Module: 9. Game State Manager
Author: Forked
Date: 2026-03-24
Purpose: Implements the utils module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

import os


def format_secs(secs):
    return "{0:.3f} secs".format(secs)


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
