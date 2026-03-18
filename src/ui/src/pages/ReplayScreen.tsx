import { useEffect, useContext, useState } from "react";
import { useParams } from "react-router-dom";
import { GridLoader } from "react-spinners";

import ZoomableBoard from "./ZoomableBoard";

import "./ReplayScreen.scss";
import LeftDrawer from "../components/LeftDrawer";
import RightDrawer from "../components/RightDrawer";
import { store } from "../store";
import ACTIONS from "../actions";
import { getState } from "../utils/apiClient";
import AnalysisBox from "../components/AnalysisBox";
import { Divider } from "@mui/material";
import ReplayBox from "../components/ReplayBox";
import PlayerStats from "../components/PlayerStats";
import ActionLog from "../components/ActionLog";

function ReplayScreen() {
  const { gameId } = useParams();
  const { state, dispatch } = useContext(store);
  const [latestStateIndex, setLatestStateIndex] = useState<number>(0);
  const [stateIndex, setStateIndex] = useState<number>(0);

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
    <>
      <AnalysisBox stateIndex={stateIndex}/>
      <Divider />
      <ReplayBox
        stateIndex={stateIndex}
        latestStateIndex={latestStateIndex}
        onNextMove={handleNextState}
        onPrevMove={handlePrevState}
        onSeekMove={(index) => setStateIndex(index)}
      />
    </>
  );

  return (
    <main className="replay-screen-main">
      <div className="desktop-layout">
        <h1 className="logo">Catan Arena</h1>
        <ZoomableBoard replayMode={true} />
        <LeftDrawer />
        <RightDrawer>
          {rightDrawerContent}
        </RightDrawer>
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
              <AnalysisBox stateIndex={stateIndex}/>
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

export default ReplayScreen;
