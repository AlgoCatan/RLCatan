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
