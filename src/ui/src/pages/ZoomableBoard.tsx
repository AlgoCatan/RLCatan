/*
Module: 6. User Interface
Author: Forked
Date: 2025-11-05
Purpose: Provides the zoomableboard module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { useCallback, useContext, useEffect, useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import memoize from "fast-memoize";
import { useMediaQuery, useTheme } from "@mui/material";

import useWindowSize from "../utils/useWindowSize";

import "./Board.scss";
import { store } from "../store";
import { isPlayersTurn } from "../utils/stateUtils";
import { postAction } from "../utils/apiClient";
import type { CatanState } from "../store";
import { useParams } from "react-router";
import ACTIONS from "../actions";
import Board from "./Board";
import type { GameAction, TileCoordinate } from "../utils/api.types";

function getMoveRobberCoordinate(action: GameAction): TileCoordinate | null {
  if (action[1] !== "MOVE_ROBBER") {
    return null;
  }

  return action[2][0];
}

/**
 * Returns object representing actions to be taken if click on node.
 * @returns {3 => ["BLUE", "BUILD_CITY", 3], ...}
 */
function buildNodeActions(state: CatanState) {
  if (!state.gameState)
    throw new Error("GameState is not ready!");

  if (!isPlayersTurn(state.gameState)) {
    return {};
  }

  const nodeActions: Record<number, GameAction> = {};
  const buildInitialSettlementActions = state.gameState.is_initial_build_phase
    ? state.gameState.current_playable_actions.filter(
        (action) => action[1] === "BUILD_SETTLEMENT"
      )
    : [];
  const inInitialBuildPhase = state.gameState.is_initial_build_phase;
  if (inInitialBuildPhase) {
    buildInitialSettlementActions.forEach((action) => {
      nodeActions[action[2]] = action;
    });
  } else if (state.isBuildingSettlement) {
    state.gameState.current_playable_actions
      .filter((action) => action[1] === "BUILD_SETTLEMENT")
      .forEach((action) => {
        nodeActions[action[2]] = action;
      });
  } else if (state.isBuildingCity) {
    state.gameState.current_playable_actions
      .filter((action) => action[1] === "BUILD_CITY")
      .forEach((action) => {
        nodeActions[action[2]] = action;
      });
  }
  return nodeActions;
}

function buildEdgeActions(state: CatanState) {
  if (!state.gameState)
    throw new Error("GameState is not ready!");
  if (!isPlayersTurn(state.gameState)) {
    return {};
  }

  const edgeActions: Record<`${number},${number}`, GameAction> = {};
  const buildInitialRoadActions = state.gameState.is_initial_build_phase
    ? state.gameState.current_playable_actions.filter(
        (action) => action[1] === "BUILD_ROAD"
      )
    : [];
  const inInitialBuildPhase = state.gameState.is_initial_build_phase;
  if (inInitialBuildPhase) {
    buildInitialRoadActions.forEach((action) => {
      edgeActions[`${action[2][0]},${action[2][1]}`] = action;
      console.log(Object.keys(edgeActions), action);
    });
  } else if (state.isBuildingRoad || state.isRoadBuilding) {
    state.gameState.current_playable_actions
      .filter((action) => action[1] === "BUILD_ROAD")
      .forEach((action) => {
        edgeActions[`${action[2][0]},${action[2][1]}`] = action;
      });
  }
  return edgeActions;
}

type ZoomableBoardProps = {
  replayMode: boolean;
}

export default function ZoomableBoard({ replayMode }: ZoomableBoardProps) {
  const { gameId } = useParams();
  const { state, dispatch } = useContext(store);
  const { width, height } = useWindowSize();
  const theme = useTheme();
  // isMobile here seems to actually match "desktop" (md and up) based on existing code. 
  // keeping it as is to avoid breaking Board component logic, but adding isSmallScreen for our layout logic.
  const isMobile = useMediaQuery(theme.breakpoints.up("md")); 
  const isSmallScreen = useMediaQuery(theme.breakpoints.down("md"));

  const [show, setShow] = useState(false);
  const gameState = state.gameState
  if (!gameState)
    throw new Error("GameState is not ready!");
  if (!gameId)
    throw new Error("expecting gameId in URL");

  // Calculate adjusted height for mobile split screen, minus 60px for header + spacing
  const boardHeight = isSmallScreen && height ? (height * 0.65) - 60 : height;

  // TODO: Move these up to GameScreen and let Zoomable be presentational component
  // https://stackoverflow.com/questions/61255053/react-usecallback-with-parameter
  const buildOnNodeClick = useCallback(
    memoize((id, action) => async () => {
      console.log("Clicked Node ", id, action);
      if (action) {
        const gameState = await postAction(gameId, action);
        dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
      }
    }),
    []
  );
  const buildOnEdgeClick = useCallback(
    memoize((id, action) => async () => {
      console.log("Clicked Edge ", id, action);
      if (action) {
        const gameState = await postAction(gameId, action);
        dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
      }
    }),
    []
  );
  const handleTileClick = useCallback(
    memoize((coordinate: TileCoordinate) => {
      console.log("Clicked Tile ", coordinate);
      if (state.isMovingRobber) {
        // Find the "MOVE_ROBBER" action in current_playable_actions that
        // corresponds to the tile coordinate selected by the user
        const matchingAction = gameState.current_playable_actions.find(
          ([, action_type, [action_coordinate, ,]]) =>
            action_type === "MOVE_ROBBER" &&
            action_coordinate.every((val: number, index: number) => val === coordinate[index])
        );
        if (matchingAction) {
          postAction(gameId, matchingAction).then((gameState) => {
            dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
          });
        }
      }
    }),
    [state.isMovingRobber]
  );

  const nodeActions = replayMode ? {} : buildNodeActions(state);
  const edgeActions = replayMode ? {} : buildEdgeActions(state);
  const validRobberCoordinates = new Set(
    state.isMovingRobber
      ? gameState.current_playable_actions
          .map(getMoveRobberCoordinate)
          .filter((coordinate): coordinate is TileCoordinate => coordinate !== null)
          .map((coordinate) => coordinate.join(","))
      : []
  );

  useEffect(() => {
    setTimeout(() => {
      setShow(true);
    }, 300);
  }, []);

  if (!width || !height) return;

  const initialScale = isSmallScreen ? 0.9 : 1;
  const initialX = isSmallScreen && width ? width * 0.05 : 0;
  
  return (
    <TransformWrapper
      initialScale={initialScale}
      {...(isSmallScreen ? { minScale: 0.5, maxScale: 1 } : {})}
      initialPositionX={initialX}
      initialPositionY={0}
      centerZoomedOut={false}
      limitToBounds={false}
    >
      <div className="board-container">
        <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }}>
          <Board
            width={width}
            height={boardHeight}
            buildOnNodeClick={buildOnNodeClick}
            buildOnEdgeClick={buildOnEdgeClick}
            handleTileClick={handleTileClick}
            nodeActions={nodeActions}
            edgeActions={edgeActions}
            replayMode={replayMode}
            show={show}
            gameState={gameState}
            isMobile={isMobile}
            isMovingRobber={state.isMovingRobber}
            validRobberCoordinates={validRobberCoordinates}
          />
        </TransformComponent>
      </div>
    </TransformWrapper>
  );
}
