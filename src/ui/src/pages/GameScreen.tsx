import { useEffect, useState, useContext, useRef, useCallback } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
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
import { type StateIndex, createGame, getState, postAction, getMoveExplanation } from "../utils/apiClient";
import { playerKey } from "../utils/stateUtils";
import AnalysisBox from "../components/AnalysisBox";
import { loadAutoGameConfig } from "../utils/autoMode";
import {
  Divider,
  Button,
  Dialog,
  DialogContent,
  DialogActions,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import PlayerStats from "../components/PlayerStats";
import ActionLog from "../components/ActionLog";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import cn from "classnames";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";

const ROBOT_THINKING_TIME = 300;

function GameScreen({ replayMode }: { replayMode: boolean }) {
  const theme = useTheme();
  // true when viewport width is <= md breakpoint
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [searchParams] = useSearchParams();
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
  const [isWinnerModalOpen, setIsWinnerModalOpen] = useState(false);
  const [isMobilePlayerInfoCollapsed, setIsMobilePlayerInfoCollapsed] = useState(false);
  const [isAutoRestarting, setIsAutoRestarting] = useState(false);
  const autoRestartedGameId = useRef<string | null>(null);
  const isAutoMode = searchParams.get("auto") === "1";

  const handleActionClick = async (index: number) => {
    if (!isExplainMode || !gameId) return;

    setIsExplainingLoading(true);
    setExplanation("Thinking...");
    // open the right drawer so users can see the result
    dispatch({ type: ACTIONS.SET_RIGHT_DRAWER_OPENED, data: true });

    try {
      const data = await getMoveExplanation(gameId, index);
      setExplanation(data.explanation ?? `No explanation returned for move ${index}`);
    } catch (err: any) {
      console.error("Failed to fetch explanation", err);

      // Provide more specific error messages based on HTTP status
      let errorMsg = "Error fetching explanation.";
      if (err.response?.status === 400) {
        errorMsg = `Move ${index} not found. Please ensure the move has been recorded.`;
      } else if (err.response?.status === 404) {
        errorMsg = "Game not found or explanation data not loaded.";
      } else if (err.response?.status === 429) {
        errorMsg = "LLM quota reached. Please try again in a moment.";
      } else if (err.response?.status === 500) {
        errorMsg = "Server error generating explanation. Please try again.";
      }

      setExplanation(errorMsg);
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
    autoRestartedGameId.current = null;
    dispatch({ type: ACTIONS.SET_GAME_STATE, data: null });

    let isCancelled = false;

    (async () => {
      const gameState = await getState(gameId, stateIndex as StateIndex);
      if (!isCancelled) {
        dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
        setIsAutoRestarting(false);
      }
    })();

    return () => {
      isCancelled = true;
    };
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

  useEffect(() => {
    if (state.gameState?.winning_color && !replayMode && !isAutoMode) {
      setIsWinnerModalOpen(true);
    }
  }, [state.gameState?.winning_color, replayMode, isAutoMode]);

  useEffect(() => {
    if (!state.gameState?.winning_color || replayMode || !isAutoMode || !gameId) {
      return;
    }
    if (autoRestartedGameId.current === gameId) {
      return;
    }

    const config = loadAutoGameConfig();
    if (!config) {
      setIsWinnerModalOpen(true);
      return;
    }

    let isCancelled = false;
    autoRestartedGameId.current = gameId;
    setIsAutoRestarting(true);

    (async () => {
      try {
        const nextGameId = await createGame(config);
        if (!isCancelled) {
          navigate(`/games/${nextGameId}?auto=1`, { replace: true });
        }
      } catch (err) {
        console.error("Failed to auto-start next game", err);
        if (!isCancelled) {
          autoRestartedGameId.current = null;
          setIsWinnerModalOpen(true);
          setIsAutoRestarting(false);
        }
      }
    })();

    return () => {
      isCancelled = true;
    };
  }, [state.gameState?.winning_color, replayMode, isAutoMode, gameId, navigate]);

  useEffect(() => {
    setIsMobilePlayerInfoCollapsed(false);
  }, [isMobile]);

  // Update rightDrawerContent to original AnalysisBox + Watch Replay + Explain Move
  const rightDrawerContent = (
    <div className="right-drawer-card game-analysis-panel">
      <div className="right-drawer-card-body" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        {/* original AnalysisBox (contains its own Analyze button) */}
        <AnalysisBox
          stateIndex={"latest"}
          companionAction={
            isMobile ? (
              <Button
                className="watch-replay-button analysis-button analysis-companion-button"
                variant="contained"
                fullWidth
                onClick={() => navigate(`/replays/${gameId}`)}
              >
                WATCH REPLAY
              </Button>
            ) : undefined
          }
        />

        <Divider style={{ margin: "12px 0" }} />

        {/* Desktop: Watch Replay + Explain Move stacked. Mobile: Explain Move only. */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {!isMobile && (
            <Button
              className="watch-replay-button analysis-button"
              variant="contained"
              fullWidth
              onClick={() => navigate(`/replays/${gameId}`)}
            >
              WATCH REPLAY
            </Button>
          )}

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
          {isExplainMode && !explanation ? (
            <div className="llm-explain-hint">
              Select a Move
            </div>
          ) : explanation ? (
            <div className="llm-output-card">
              <div className="llm-header">AI EXPLANATION</div>
              <div className="llm-body">{isExplainingLoading ? "Generating insights..." : explanation}</div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );

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

  const winnerColor = state.gameState.winning_color;
  const winnerKey =
    winnerColor !== undefined ? playerKey(state.gameState, winnerColor) : null;
  const winnerName =
    winnerColor && state.gameState.player_models?.[winnerColor]
      ? state.gameState.player_models[winnerColor]
      : winnerColor;
  const winnerStats =
    winnerKey && winnerColor
      ? {
          knights: state.gameState.player_state[`${winnerKey}_PLAYED_KNIGHT`],
          roads: state.gameState.player_state[`${winnerKey}_LONGEST_ROAD_LENGTH`],
          vps: state.gameState.player_state[`${winnerKey}_ACTUAL_VICTORY_POINTS`],
        }
      : null;

  return (
    <main className={cn("game-screen-main", { "right-drawer-open": state.isRightDrawerOpen })}>
      <Dialog
        open={isWinnerModalOpen && Boolean(winnerColor)}
        onClose={() => setIsWinnerModalOpen(false)}
        fullWidth
        maxWidth="xs"
        PaperProps={{ className: "winner-modal-paper" }}
      >
        <DialogContent className="winner-modal-content">
          <div className="winner-modal-icon">
            <EmojiEventsIcon fontSize="inherit" />
          </div>
          <div className="winner-modal-title">Winner</div>
          <div className="winner-modal-name">
            {winnerName}
            {winnerColor ? (
              <span className={`winner-modal-color ${winnerColor.toLowerCase()}`}>
                {winnerColor}
              </span>
            ) : null}
          </div>
          {winnerStats && (
            <div className="winner-modal-stats">
              <div className="winner-stat">
                <strong>{winnerStats.knights}</strong>
                <span>Knights</span>
              </div>
              <div className="winner-stat">
                <strong>{winnerStats.roads}</strong>
                <span>Roads</span>
              </div>
              <div className="winner-stat">
                <strong>{winnerStats.vps}</strong>
                <span>VPs</span>
              </div>
            </div>
          )}
        </DialogContent>
        <DialogActions className="winner-modal-actions">
          <Button onClick={() => setIsWinnerModalOpen(false)}>Close</Button>
          <Button onClick={() => navigate("/")}>Play Again</Button>
          <Button
            variant="contained"
            onClick={() => navigate(`/replays/${gameId}`)}
          >
            Watch Replay
          </Button>
        </DialogActions>
      </Dialog>
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

          {/* Two-column bottom row: left = PlayerStats + ActionLog (stacked), right = right-drawer content */}
          <div className="mobile-drawers-row">
            <div className="mobile-left-drawer-content">
              <div className={cn("mobile-left-top", { collapsed: isMobilePlayerInfoCollapsed })}>
                <button
                  type="button"
                  className="mobile-player-toggle"
                  aria-expanded={!isMobilePlayerInfoCollapsed}
                  aria-label={isMobilePlayerInfoCollapsed ? "Show player info" : "Hide player info"}
                  onClick={() => setIsMobilePlayerInfoCollapsed((current) => !current)}
                >
                  <span>Player Info</span>
                  <KeyboardArrowDownIcon
                    className={cn("mobile-player-toggle-icon", {
                      open: !isMobilePlayerInfoCollapsed,
                    })}
                  />
                </button>
                <div className="mobile-player-panel">
                  <PlayerStats gameState={state.gameState} />
                </div>
              </div>
              <div className="mobile-left-bottom">
                <ActionLog
                  gameState={state.gameState}
                  isExplainMode={isExplainMode}
                  onActionClick={handleActionClick}
                />
              </div>
            </div>
            <div className="mobile-right-drawer-content">
               {rightDrawerContent}
            </div>
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
