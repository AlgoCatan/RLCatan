import cn from "classnames";
import { humanizeAction } from "../utils/promptUtils";
import { type GameState } from "../utils/api.types";
import "./ActionLog.scss";

export default function ActionLog({ gameState }: { gameState: GameState }) {
  if (!gameState) return null;
  return (
      <div className="log">
        {gameState.actions
          .slice()
          .reverse()
          .map((action, i) => (
            <div key={i} className={cn("action foreground", action[0])}>
              {humanizeAction(gameState, action)}
            </div>
          ))}
      </div>
  );
}
