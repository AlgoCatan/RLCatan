/*
Module: 6. User Interface
Author: Forked
Date: 2025-11-04
Purpose: Provides the actionlog module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import cn from "classnames";
import { humanizeAction } from "../utils/promptUtils";
import { type GameState } from "../utils/api.types";
import "./ActionLog.scss";

export default function ActionLog({
  gameState,
  isExplainMode = false,
  onActionClick,
}: {
  gameState: GameState;
  isExplainMode?: boolean;
  onActionClick?: (index: number) => void;
}) {
  if (!gameState) return null;
  const totalActions = gameState.actions.length;

  return (
    <div className={cn("log", { "explain-mode-active": isExplainMode })}>
      {gameState.actions
        .slice()
        .reverse()
        .map((action, i) => {
          // original index (0-based) in chronological order
          const originalIndex = totalActions - 1 - i;
          return (
            <div
              key={originalIndex}
              className={cn("action foreground", action[0], {
                clickable: isExplainMode,
              })}
              onClick={() =>
                isExplainMode && onActionClick && onActionClick(originalIndex)
              }
            >
              <span className="move-number">#{originalIndex + 1}</span>{" "}
              {humanizeAction(gameState, action)}
            </div>
          );
        })}
    </div>
  );
}
