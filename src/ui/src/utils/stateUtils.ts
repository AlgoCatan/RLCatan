/*
Module: 6. User Interface
Author: Forked
Date: 2026-03-09
Purpose: Provides the stateutils module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import type { Color, GameState } from "./api.types";

/**
 * Check if it's a human player's turn
 * @param gameState
 * @returns True if a human player needs to play
 */
export function isPlayersTurn(gameState: GameState): boolean {
  return !gameState.bot_colors.includes(gameState.current_color);
}

export function playerKey(gameState: GameState, color: Color): string {
  return `P${gameState.colors.indexOf(color)}`;
}

export function getHumanColor(gameState: GameState): Color {
  return gameState.colors.find(
    (color) => !gameState.bot_colors.includes(color)
  ) as Color;
}
