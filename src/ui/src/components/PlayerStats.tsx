import React from "react";
import Divider from "@mui/material/Divider";
import PlayerStateBox from "./PlayerStateBox";
import { playerKey } from "../utils/stateUtils";
import { type GameState } from "../utils/api.types";

export default function PlayerStats({ gameState }: { gameState: GameState }) {
  if (!gameState) return null;
  return (
    <div className="player-stats">
      {gameState.colors.map((color) => {
        const key = playerKey(gameState, color);
        return (
          <React.Fragment key={color}>
            <PlayerStateBox
              playerState={gameState.player_state}
              playerKey={key}
              color={color}
              botName={gameState.player_models?.[color]}
            />
            <Divider />
          </React.Fragment>
        );
      })}
    </div>
  );
}
