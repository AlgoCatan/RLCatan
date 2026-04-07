/*
Module: 6. User Interface
Author: Forked
Date: 2026-02-27
Purpose: Provides the gamescreenutils module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import type { GameState } from "../utils/api.types";

export function getActiveGameState(
  routeGameId: string | undefined,
  loadedGameId: string | null,
  gameState: GameState | null
): GameState | null {
  if (!routeGameId || loadedGameId !== routeGameId) {
    return null;
  }

  return gameState;
}
