import { describe, expect, test } from "vitest";

import { getActiveGameState } from "./gameScreenUtils";
import type { GameState } from "../utils/api.types";

const mockGameState = {
  tiles: [],
  adjacent_tiles: {},
  bot_colors: ["RED", "BLUE"],
  colors: ["RED", "BLUE"],
  player_models: {},
  current_color: "RED",
  winning_color: "RED",
  current_prompt: "PLAY_TURN",
  player_state: {},
  actions: [],
  robber_coordinate: [0, 0, 0],
  nodes: [],
  edges: [],
  current_playable_actions: [],
  is_initial_build_phase: false,
  state_index: 42,
} satisfies GameState;

describe("getActiveGameState", () => {
  test("returns null while the current route is still loading a different game", () => {
    expect(getActiveGameState("next-game", "finished-game", mockGameState)).toBeNull();
  });

  test("returns the state once the loaded game matches the route", () => {
    expect(getActiveGameState("finished-game", "finished-game", mockGameState)).toBe(
      mockGameState
    );
  });
});
