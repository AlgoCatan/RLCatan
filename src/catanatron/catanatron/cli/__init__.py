"""
Module: 9. Game State Manager
Author: Forked
Date: 2025-11-08
Purpose: Implements the package initializer module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

from catanatron.cli.simulation_accumulator import SimulationAccumulator


def register_cli_player(*args, **kwargs):
    from catanatron.cli.cli_players import register_cli_player as _register_cli_player

    return _register_cli_player(*args, **kwargs)


def register_cli_accumulator(*args, **kwargs):
    from catanatron.cli.cli_players import (
        register_cli_accumulator as _register_cli_accumulator,
    )

    return _register_cli_accumulator(*args, **kwargs)
