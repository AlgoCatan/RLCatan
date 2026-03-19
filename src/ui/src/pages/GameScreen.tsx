import { useEffect, useState, useContext, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { GridLoader } from "react-spinners";
import { useSnackbar } from "notistack";

import ZoomableBoard from "./ZoomableBoard";
import ActionsToolbar from "./ActionsToolbar";

import "./GameScreen.scss";
import LeftDrawer from "../components/LeftDrawer";
import RightDrawer from "../components/RightDrawer";
import { store } from "../store";
import ACTIONS from "../actions";
import { type StateIndex, getState, postAction } from "../utils/apiClient";
import { dispatchSnackbar } from "../components/Snackbar";
import { getHumanColor } from "../utils/stateUtils";
import AnalysisBox from "../components/AnalysisBox";
import { Divider, Button } from "@mui/material";
import PlayerStats from "../components/PlayerStats";
import ActionLog from "../components/ActionLog";

const ROBOT_THINKING_TIME = 300;

function GameScreen({ replayMode }: { replayMode: boolean }) {
  const { gameId, stateIndex } = useParams();
  const navigate = useNavigate();
  const { state, dispatch } = useContext(store);
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const [isBotThinking, setIsBotThinking] = useState(false);
  const lastProcessedStateIndex = useRef(-1);

  // Load game state
  useEffect(() => {
    if (!gameId) {
      return;
    }
    lastProcessedStateIndex.current = -1;

    (async () => {
      const gameState = await getState(gameId, stateIndex as StateIndex);
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    })();
  }, [gameId, stateIndex, dispatch]);

  // Maybe kick off next query?
  useEffect(() => {
    if (!state.gameState || replayMode || !gameId) {
      return;
    }
    if (
      state.gameState.bot_colors.includes(state.gameState.current_color) &&
      !state.gameState.winning_color
    ) {
      if (lastProcessedStateIndex.current === state.gameState.state_index) {
        return;
      }
      lastProcessedStateIndex.current = state.gameState.state_index;

      // Make bot click next action.
      (async () => {
        setIsBotThinking(true);
        const start = new Date();
        const gameState = await postAction(gameId);
        const requestTime = new Date().valueOf() - start.valueOf();
        setTimeout(() => {
          // simulate thinking
          setIsBotThinking(false);
          dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
          // Commented out dispatchSnackbar
          // if (getHumanColor(gameState)) {
          //   dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
          // }
        }, ROBOT_THINKING_TIME - requestTime);
      })();
    }
  }, [
    gameId,
    replayMode,
    state.gameState,
    dispatch,
    enqueueSnackbar,
    closeSnackbar,
  ]);

  if (!state.gameState) {
    return (
      <main>
        <GridLoader
          className="loader"
          color="#000000"
          size={100}
        />
      </main>
    );
  }

  const rightDrawerContent = (
    <div className="right-drawer-card">
      <div className="right-drawer-card-body">
        <AnalysisBox stateIndex={"latest"} />
        <Divider />
        <Button
          className="watch-replay-button"
          variant="contained"
          onClick={() => navigate(`/replays/${gameId}`)}
        >
          Watch Replay
        </Button>
      </div>
    </div>
  );

  return (
    <main className="game-screen-main">
      <div className="desktop-layout">
        <h1 className="logo">Catan Arena</h1>
        <ZoomableBoard replayMode={replayMode} />
        <ActionsToolbar
          isBotThinking={isBotThinking}
          replayMode={replayMode}
          rightDrawerContent={rightDrawerContent}
        />
        <LeftDrawer />
        <RightDrawer inlineOnDesktop={true}>
          {rightDrawerContent}
        </RightDrawer>
      </div>

      <div className="mobile-layout">
        <div className="mobile-top-half">
          <h1 className="logo">Catan Arena</h1>
          <div className="zoomable-wrapper" style={{ flex: 1, position: 'relative', width: '100%', overflow: 'hidden' }}>
             <ZoomableBoard replayMode={replayMode} />
          </div>
        </div>
        <div className="mobile-bottom-half">
          <ActionsToolbar isBotThinking={isBotThinking} replayMode={replayMode} />
          <div className="mobile-drawers-row">
            <div className="mobile-left-drawer-content">
               <PlayerStats gameState={state.gameState} />
            </div>
            <div className="mobile-right-drawer-content">
               {rightDrawerContent}
            </div>
          </div>
          <div className="mobile-action-log">
             <ActionLog gameState={state.gameState} />
          </div>
        </div>
      </div>
    </main>
  );
}

GameScreen.propTypes = {
  /**
   * Injected by the documentation to work in an iframe.
   * You won't need it on your project.
   */
  window: PropTypes.func,
};

export default GameScreen;
