"""
Module: 9. Game State Manager
Author: Forked
Date: 2025-12-11
Purpose: Implements the gym example module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

import random
import gymnasium
import catanatron.gym

env = gymnasium.make("catanatron/Catanatron-v0")
observation, info = env.reset()
for _ in range(1000):
    # your agent here (this takes random actions)
    action = random.choice(info["valid_actions"])

    observation, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    if done:
        observation, info = env.reset()
env.close()
