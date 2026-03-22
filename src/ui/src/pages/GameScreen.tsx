import { useEffect, useState, useContext, useRef, useCallback } from "react";
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
import { type StateIndex, getState, postAction, getMoveExplanation } from "../utils/apiClient";
import { dispatchSnackbar } from "../components/Snackbar";
import { getHumanColor } from "../utils/stateUtils";
import AnalysisBox from "../components/AnalysisBox";
import { Divider, Button, useTheme, useMediaQuery } from "@mui/material";
import PlayerStats from "../components/PlayerStats";
import ActionLog from "../components/ActionLog";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import cn from "classnames";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";

const ROBOT_THINKING_TIME = 300;

function GameScreen({ replayMode }: { replayMode: boolean }) {
  const theme = useTheme();
  // true when viewport width is <= md breakpoint
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const { gameId, stateIndex } = useParams();
  const navigate = useNavigate();
  const { state, dispatch } = useContext(store);
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const [isBotThinking, setIsBotThinking] = useState(false);
  const lastProcessedStateIndex = useRef(-1);

  // Explain-mode state + explanation storage
  const [isExplainMode, setIsExplainMode] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isExplainingLoading, setIsExplainingLoading] = useState(false);

  const handleActionClick = async (index: number) => {
    if (!isExplainMode || !gameId) return;

    setIsExplainingLoading(true);
    setExplanation("Thinking...");
    // open the right drawer so users can see the result
    dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: true });

    try {
      const data = await getMoveExplanation(gameId, index);
      setExplanation(data.explanation ?? `No explanation returned for move ${index}`);
    } catch (err) {
      console.error("Failed to fetch explanation", err);
      setExplanation("Error fetching explanation.");
    } finally {
      setIsExplainingLoading(false);
    }
  };

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

  // Update rightDrawerContent to original AnalysisBox + Watch Replay + Explain Move
  const rightDrawerContent = (
    <div className="right-drawer-card">
      <div className="right-drawer-card-body" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        {/* original AnalysisBox (contains its own Analyze button) */}
        <AnalysisBox stateIndex={"latest"} />

        <Divider style={{ margin: "12px 0" }} />

        {/* Watch Replay + Explain Move stacked */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <Button
            className="watch-replay-button"
            variant="contained"
            fullWidth
            onClick={() => navigate(`/replays/${gameId}`)}
          >
            WATCH REPLAY
          </Button>

          <Button
            className={`explain-move-button ${isExplainMode ? "active" : ""}`}
            variant={isExplainMode ? "contained" : "outlined"}
            color={isExplainMode ? "secondary" : "inherit"}
            fullWidth
            startIcon={<HelpOutlineIcon />}
            onClick={() => {
              const next = !isExplainMode;
              setIsExplainMode(next);
              // If we're turning explain mode OFF (Cancel Explain), clear the explanation
              if (!next) setExplanation(null);
            }}
          >
            {isExplainMode ? "CANCEL EXPLAIN" : "EXPLAIN MOVE"}
          </Button>
        </div>

        {/* Explanation / results area */}
        <div style={{ marginTop: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
          {explanation && (
            <div className="llm-output-card">
              <div className="llm-header">AI EXPLANATION</div>
              <div className="llm-body">{isExplainingLoading ? "Generating insights..." : explanation}</div>
              <div style={{ marginTop: 8 }}>
                <Button size="small" onClick={() => setExplanation(null)}>Clear</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const openRightDrawer = useCallback(() => {
    dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: true });
  }, [dispatch]);

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

  return (
    <main className={cn("game-screen-main", { "right-drawer-open": state.isRightDrawerOpen })}>
      {/* Explanation is shown in the RightDrawer (see rightDrawerContent) */}

      <div className="desktop-layout">
        <h1 className="logo">Catan Arena</h1>
        {/* Desktop-only: single fixed blue tab to open the right drawer when closed.
            This is the ONLY way to open the right drawer on desktop. */}
        {!isMobile && !state.isRightDrawerOpen && (
          <Button
            aria-label="Open analysis"
            variant="contained"
            onClick={() => dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: true })}
            sx={{
              position: "fixed",
              top: "50%",
              right: 0,
              transform: "translateY(-50%)",
              zIndex: 1200,
              minWidth: 36,
              width: 44,
              height: 72,
              padding: 0,
              borderRadius: "8px 0 0 8px",
              backgroundColor: "#1565c0",
              boxShadow: "-2px 0 14px rgba(0,0,0,0.35)",
              "&:hover": { backgroundColor: "#0d47a1" },
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.1rem",
            }}
          >
            <ChevronLeftIcon fontSize="large" />
          </Button>
        )}
        <ZoomableBoard replayMode={replayMode} />
        <ActionsToolbar
          isBotThinking={isBotThinking}
          replayMode={replayMode}
        />
        {/* pass explain props to left drawer so desktop log entries become clickable */}
        <LeftDrawer
          isExplainMode={isExplainMode}
          onActionClick={handleActionClick}
        />
        {/* RightDrawer now contains the Explain Move toggle and explanation content */}
        <RightDrawer>
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
          {/* Explanation shown in RightDrawer (mobile users can open the drawer to view) */}

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
             {/* pass explain-mode and handler to action log used on mobile */}
             <ActionLog
               gameState={state.gameState}
               isExplainMode={isExplainMode}
               onActionClick={handleActionClick}
             />
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
