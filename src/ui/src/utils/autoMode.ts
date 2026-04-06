import type { CreateGameOptions } from "./apiClient";

const AUTO_GAME_CONFIG_KEY = "catan_arena_auto_game_config";

export type AutoGameConfig = CreateGameOptions;

export function saveAutoGameConfig(config: AutoGameConfig) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(AUTO_GAME_CONFIG_KEY, JSON.stringify(config));
}

export function loadAutoGameConfig(): AutoGameConfig | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTO_GAME_CONFIG_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AutoGameConfig;
  } catch {
    return null;
  }
}

export function clearAutoGameConfig() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTO_GAME_CONFIG_KEY);
}
