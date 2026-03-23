import React, { useCallback, useContext } from "react";
import cn from "classnames";
import SwipeableDrawer from "@mui/material/SwipeableDrawer";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import { useTheme, useMediaQuery } from "@mui/material";

import Hidden from "./Hidden";
import PlayerStateBox from "./PlayerStateBox";
import { humanizeAction } from "../utils/promptUtils";
import { store } from "../store";
import ACTIONS from "../actions";
import { playerKey } from "../utils/stateUtils";
import { type GameState } from "../utils/api.types";
import { isTabOrShift, type InteractionEvent } from "../utils/events";

import "./LeftDrawer.scss";

function DrawerContent({
  gameState,
  isExplainMode,
  onActionClick,
}: {
  gameState: GameState;
  isExplainMode?: boolean;
  onActionClick?: (index: number) => void;
}) {
  const totalActions = gameState.actions.length;

  const playerSections = gameState.colors.map((color) => {
    const key = playerKey(gameState, color);
    return (
      <React.Fragment key={color}>
        <div className="player-section">
          <PlayerStateBox
            playerState={gameState.player_state}
            playerKey={key}
            color={color}
            botName={gameState.player_models?.[color]}
          />
        </div>
        <Divider />
      </React.Fragment>
    );
  });

  return (
    <>
      {playerSections}
      <div className={cn("log", { "explain-mode-active": isExplainMode })}>
        {gameState.actions
          .slice()
          .reverse()
          .map((action, i) => {
            // original index (0-based) in the chronological actions array
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
    </>
  );
}

export default function LeftDrawer({
  isExplainMode,
  onActionClick,
}: {
  isExplainMode?: boolean;
  onActionClick?: (index: number) => void;
}) {
  const { state, dispatch } = useContext(store);
  const iOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const openLeftDrawer = useCallback(
    (event: InteractionEvent) => {
      if (isTabOrShift(event)) {
        return;
      }

      dispatch({ type: ACTIONS.SET_LEFT_DRAWER_OPENED, data: true });
    },
    [dispatch]
  );
  const closeLeftDrawer = useCallback(
    (event: InteractionEvent) => {
      if (isTabOrShift(event)) {
        return;
      }

      dispatch({ type: ACTIONS.SET_LEFT_DRAWER_OPENED, data: false });
    },
    [dispatch]
  );

  return (
    <>
      {isMobile ? (
        <SwipeableDrawer
          className="left-drawer"
          anchor="left"
          open={state.isLeftDrawerOpen}
          onClose={closeLeftDrawer}
          onOpen={openLeftDrawer}
          disableBackdropTransition={!iOS}
          disableDiscovery={iOS}
          onKeyDown={closeLeftDrawer}
        >
          <DrawerContent gameState={state.gameState as GameState} isExplainMode={isExplainMode} onActionClick={onActionClick} />
        </SwipeableDrawer>
      ) : (
        <Drawer className="left-drawer" anchor="left" variant="permanent" open>
          <DrawerContent gameState={state.gameState as GameState} isExplainMode={isExplainMode} onActionClick={onActionClick} />
        </Drawer>
      )}
    </>
  );
}
