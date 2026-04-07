"""
Module: 2. Training Pipeline
Author: Forked
Date: 2025-11-29
Purpose: Implements the package initializer module for the training pipeline, supporting reinforcement-learning environments, wrappers, rewards, or training data flow.
"""

from gymnasium.envs.registration import register

register(
    id="catanatron/Catanatron-v0",
    entry_point="catanatron.gym.envs:CatanatronEnv",
)
