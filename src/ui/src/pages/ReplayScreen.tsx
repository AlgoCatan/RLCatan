import { useEffect, useContext, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { GridLoader } from "react-spinners";
import { Button, useTheme, useMediaQuery } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";

import ZoomableBoard from "./ZoomableBoard";

import "./ReplayScreen.scss";
import LeftDrawer from "../components/LeftDrawer";
import RightDrawer from "../components/RightDrawer";
import { store } from "../store";
import ACTIONS from "../actions";
import { getState, getMoveExplanation } from "../utils/apiClient";
import AnalysisBox from "../components/AnalysisBox";
import { Divider } from "@mui/material";
import ReplayBox from "../components/ReplayBox";
import PlayerStats from "../components/PlayerStats";
import ActionLog from "../components/ActionLog";

function ReplayScreen() {
  const { gameId } = useParams();
  const { state, dispatch } = useContext(store);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [latestStateIndex, setLatestStateIndex] = useState<number>(0);
  const [stateIndex, setStateIndex] = useState<number>(0);
  const [isExplainMode, setIsExplainMode] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isExplainingLoading, setIsExplainingLoading] = useState(false);

  const handleActionClick = useCallback(
    async (index: number) => {
      if (!isExplainMode || !gameId) return;
      setIsExplainingLoading(true);
      setExplanation("Thinking...");
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
    },
    [isExplainMode, gameId, dispatch]
  );

  const handlePrevState = () => setStateIndex((prev) => Math.max(prev - 1, 0));
  const handleNextState = () => setStateIndex((prev) => Math.min(prev + 1, latestStateIndex));

  useEffect(() => {
    if (!gameId) return;

    (async () => {
      const latestState = await getState(gameId, "latest");
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: latestState });
      setLatestStateIndex(latestState.state_index);
    })();
  }, [gameId, dispatch]);

  useEffect(() => {
    if (!gameId) {
      return;
    }

    (async () => {
      const gameState = await getState(gameId, stateIndex);
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    })();
  }, [gameId, stateIndex, dispatch]);

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
      <div className="right-drawer-card-body" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
        <AnalysisBox stateIndex={stateIndex} />
        <Divider style={{ margin: "12px 0" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <ReplayBox
            stateIndex={stateIndex}
            latestStateIndex={latestStateIndex}
            onNextMove={handleNextState}
            onPrevMove={handlePrevState}
            onSeekMove={(index) => setStateIndex(index)}
            compact={false}
          />

          <Button
            className={`explain-move-button ${isExplainMode ? "active" : ""}`}
            variant={isExplainMode ? "contained" : "outlined"}
            color={isExplainMode ? "secondary" : "inherit"}
            fullWidth
            startIcon={<HelpOutlineIcon />}
            onClick={() => {
              const next = !isExplainMode;
              setIsExplainMode(next);
              if (!next) setExplanation(null);
            }}
          >
            {isExplainMode ? "CANCEL EXPLAIN" : "EXPLAIN MOVE"}
          </Button>
        </div>

        <div style={{ marginTop: 12, flex: 1, minHeight: 0, overflow: "auto" }}>
          {isExplainMode && !explanation ? (
            <div className="llm-explain-hint">
              Please select a move from the list of moves taken
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

  return (
    <main className="replay-screen-main">
      <div className="desktop-layout">
        <h1 className="logo">Catan Arena</h1>
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
            }}
          >
            <ChevronLeftIcon fontSize="large" />
          </Button>
        )}
        <ZoomableBoard replayMode={true} />
        <LeftDrawer isExplainMode={isExplainMode} onActionClick={handleActionClick} />
        <RightDrawer>{rightDrawerContent}</RightDrawer>
      </div>

      <div className="mobile-layout">
        <div className="mobile-top-half">
          <h1 className="logo">Catan Arena</h1>
          <div className="zoomable-wrapper" style={{ flex: 1, position: "relative", width: "100%", overflow: "hidden" }}>
            <ZoomableBoard replayMode={true} />
          </div>
        </div>
        <div className="mobile-bottom-half">
          <div className="mobile-replay-controls">
            <ReplayBox
              stateIndex={stateIndex}
              latestStateIndex={latestStateIndex}
              onNextMove={handleNextState}
              onPrevMove={handlePrevState}
              onSeekMove={(index) => setStateIndex(index)}
              compact
            />
          </div>
          <div className="mobile-drawers-row">
            <div className="mobile-left-drawer-content">
              <PlayerStats gameState={state.gameState} />
            </div>
            <div className="mobile-right-drawer-content">
              {rightDrawerContent}
            </div>
          </div>
          <div className="mobile-action-log">
            <ActionLog gameState={state.gameState} isExplainMode={isExplainMode} onActionClick={handleActionClick} />
          </div>
        </div>
      </div>
    </main>
  );
}

export default ReplayScreen;
