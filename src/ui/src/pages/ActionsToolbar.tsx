/*
Module: 6. User Interface
Author: Forked
Date: 2026-03-16
Purpose: Provides the actionstoolbar module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import React, {
  useState,
  useRef,
  useEffect,
  useContext,
  useCallback,
} from "react";
import memoize from "fast-memoize";
import { Button } from "@mui/material";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import AccountBalanceIcon from "@mui/icons-material/AccountBalance";
import BuildIcon from "@mui/icons-material/Build";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";
import MenuItem from "@mui/material/MenuItem";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Grow from "@mui/material/Grow";
import Paper from "@mui/material/Paper";
import Popper from "@mui/material/Popper";
import MenuList from "@mui/material/MenuList";
import SimCardIcon from "@mui/icons-material/SimCard";
import { useParams } from "react-router";

import Hidden from "../components/Hidden";
import Prompt from "../components/Prompt";
import ResourceCards from "../components/ResourceCards";
import ResourceSelector from "../components/ResourceSelector";
import { store } from "../store";
import ACTIONS from "../actions";
import type { Color, GameAction, ResourceCard } from "../utils/api.types";
import { getHumanColor, playerKey } from "../utils/stateUtils";
import { postAction } from "../utils/apiClient";
import { humanizeTradeAction } from "../utils/promptUtils";

import "./ActionsToolbar.scss";
import { useSnackbar } from "notistack";
import { dispatchSnackbar } from "../components/Snackbar";

import diceIcon from "../assets/dice.svg";
import robberIcon from "../assets/robber.svg";

const DICE_PIP_LAYOUTS: Record<number, string[]> = {
  1: ["center"],
  2: ["top-left", "bottom-right"],
  3: ["top-left", "center", "bottom-right"],
  4: ["top-left", "top-right", "bottom-left", "bottom-right"],
  5: ["top-left", "top-right", "center", "bottom-left", "bottom-right"],
  6: [
    "top-left",
    "top-right",
    "middle-left",
    "middle-right",
    "bottom-left",
    "bottom-right",
  ],
};

function DiceFace({ value }: { value: number }) {
  return (
    <div className="dice-roll-face">
      {DICE_PIP_LAYOUTS[value]?.map((position) => (
        <span
          key={`${value}-${position}`}
          className={`dice-roll-pip ${position}`}
        />
      ))}
    </div>
  );
}

function DiceRollPreview({
  values,
  rollerColor,
}: {
  values: [number, number];
  rollerColor: Color;
}) {
  const total = values[0] + values[1];

  return (
    <div
      className={`dice-roll-preview roller-${rollerColor.toLowerCase()}`}
      aria-hidden="true"
    >
      <div className="dice-roll-total">{total}</div>
      <div className="dice-roll-values">
        {values.map((value, index) => (
          <DiceFace key={`${value}-${index}`} value={value} />
        ))}
      </div>
    </div>
  );
}

type DicePreviewState = {
  values: [number, number];
  rollerColor: Color;
  rollId: number;
  anchor: "turn-action" | "toolbar";
};

function PlayButtons({ dicePreview }: { dicePreview: DicePreviewState | null }) {
  const { gameId } = useParams();
  if (!gameId) {
    console.error("Game ID is not found in URL parameters.");
    return null;
  }
  const { state, dispatch } = useContext(store);
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const [resourceSelectorOpen, setResourceSelectorOpen] = useState(false);

  const carryOutAction = useCallback(
    memoize((action?: GameAction) => async () => {
      const gameState = await postAction(gameId, action);
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
      // Commented out dispatchSnackbar
      // dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
    }),
    [enqueueSnackbar, closeSnackbar]
  );

  const {
    gameState,
    isPlayingMonopoly,
    isPlayingYearOfPlenty,
    isRoadBuilding,
  } = state;
  if (gameState === null) {
    return null;
  }
  const key = playerKey(gameState, gameState.current_color);
  const isRoll =
    gameState.current_prompt === "PLAY_TURN" &&
    !gameState.player_state[`${key}_HAS_ROLLED`];
  const isDiscard = gameState.current_prompt === "DISCARD";
  const isMoveRobber = gameState.current_prompt === "MOVE_ROBBER";
  const isPlayingDevCard =
    isPlayingMonopoly || isPlayingYearOfPlenty || isRoadBuilding;
  const playableDevCardTypes = new Set(
    gameState.current_playable_actions
      .filter((action) => action[1].startsWith("PLAY"))
      .map((action) => action[1])
  );
  const humanColor = getHumanColor(gameState);
  const setIsPlayingMonopoly = useCallback(() => {
    dispatch({ type: ACTIONS.SET_IS_PLAYING_MONOPOLY });
  }, [dispatch]);
  const getValidYearOfPlentyOptions = useCallback(() => {
    return gameState.current_playable_actions
      .filter((action) => action[1] === "PLAY_YEAR_OF_PLENTY")
      .map((action) => action[2]);
  }, [gameState.current_playable_actions]);
  const getDiscardOptions = useCallback(() => {
    return gameState.current_playable_actions
      .filter((action) => action[1] === "DISCARD" && action[2] !== null)
      .map((action) => action[2] as ResourceCard);
  }, [gameState.current_playable_actions]);
  const handleResourceSelection = useCallback(
    async (selectedResources: ResourceCard | ResourceCard[]) => {
      setResourceSelectorOpen(false);
      let action: GameAction;
      if (isDiscard) {
        action = [humanColor, "DISCARD", selectedResources as ResourceCard];
      } else if (isPlayingMonopoly) {
        action = [
          humanColor,
          "PLAY_MONOPOLY",
          selectedResources as ResourceCard,
        ];
      } else if (isPlayingYearOfPlenty) {
        action = [
          humanColor,
          "PLAY_YEAR_OF_PLENTY",
          selectedResources as [ResourceCard] | [ResourceCard, ResourceCard],
        ];
      } else {
        console.error("Invalid resource selector mode");
        return;
      }
      const gameState = await postAction(gameId, action);
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
      dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
    },
    [
      gameId,
      humanColor,
      dispatch,
      enqueueSnackbar,
      closeSnackbar,
      isDiscard,
      isPlayingMonopoly,
      isPlayingYearOfPlenty,
    ]
  );
  const handleOpenResourceSelector = useCallback(() => {
    setResourceSelectorOpen(true);
  }, []);
  const setIsPlayingYearOfPlenty = useCallback(() => {
    dispatch({ type: ACTIONS.SET_IS_PLAYING_YEAR_OF_PLENTY });
  }, [dispatch]);
  const playRoadBuilding = useCallback(async () => {
    const action: GameAction = [humanColor, "PLAY_ROAD_BUILDING", null];
    const gameState = await postAction(gameId, action);
    dispatch({ type: ACTIONS.PLAY_ROAD_BUILDING });
    dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
  }, [gameId, dispatch, enqueueSnackbar, closeSnackbar, humanColor]);
  const playKnightCard = useCallback(async () => {
    const action: GameAction = [humanColor, "PLAY_KNIGHT_CARD", null];
    const gameState = await postAction(gameId, action);
    dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
  }, [gameId, dispatch, enqueueSnackbar, closeSnackbar, humanColor]);
  const useItems = [
    {
      label: "Monopoly",
      disabled: !playableDevCardTypes.has("PLAY_MONOPOLY"),
      onClick: setIsPlayingMonopoly,
    },
    {
      label: "Year of Plenty",
      disabled: !playableDevCardTypes.has("PLAY_YEAR_OF_PLENTY"),
      onClick: setIsPlayingYearOfPlenty,
    },
    {
      label: "Road Building",
      disabled: !playableDevCardTypes.has("PLAY_ROAD_BUILDING"),
      onClick: playRoadBuilding,
    },
    {
      label: "Knight",
      disabled: !playableDevCardTypes.has("PLAY_KNIGHT_CARD"),
      onClick: playKnightCard,
    },
  ];

  const buildActionTypes = new Set(
    gameState.is_initial_build_phase
      ? []
      : gameState.current_playable_actions
          .filter(
            (action) =>
              action[1].startsWith("BUY") || action[1].startsWith("BUILD")
          )
          .map((a) => a[1])
  );
  const buyDevCard = useCallback(async () => {
    const action: GameAction = [humanColor, "BUY_DEVELOPMENT_CARD", null];
    const gameState = await postAction(gameId, action);
    dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
  }, [gameId, dispatch, enqueueSnackbar, closeSnackbar, humanColor]);
  const setIsBuildingSettlement = useCallback(() => {
    dispatch({ type: ACTIONS.SET_IS_BUILDING_SETTLEMENT });
  }, [dispatch]);
  const setIsBuildingCity = useCallback(() => {
    dispatch({ type: ACTIONS.SET_IS_BUILDING_CITY });
  }, [dispatch]);
  const toggleBuildingRoad = useCallback(() => {
    dispatch({ type: ACTIONS.TOGGLE_BUILDING_ROAD });
  }, [dispatch]);
  const buildItems = [
    {
      label: "Development Card",
      disabled: !buildActionTypes.has("BUY_DEVELOPMENT_CARD"),
      onClick: buyDevCard,
    },
    {
      label: "City",
      disabled: !buildActionTypes.has("BUILD_CITY"),
      onClick: setIsBuildingCity,
    },
    {
      label: "Settlement",
      disabled: !buildActionTypes.has("BUILD_SETTLEMENT"),
      onClick: setIsBuildingSettlement,
    },
    {
      label: "Road",
      disabled: !buildActionTypes.has("BUILD_ROAD"),
      onClick: toggleBuildingRoad,
    },
  ];

  const tradeActions = gameState.current_playable_actions.filter(
    (action) => action[1] === "MARITIME_TRADE"
  );
  const tradeItems = React.useMemo(() => {
    const items = tradeActions.map((action) => {
      const label = humanizeTradeAction(action);
      return {
        label: label,
        disabled: false,
        onClick: carryOutAction(action),
      };
    });

    return items.sort((a, b) => a.label.localeCompare(b.label));
  }, [tradeActions, carryOutAction]);

  const setIsMovingRobber = useCallback(() => {
    dispatch({ type: ACTIONS.SET_IS_MOVING_ROBBER });
  }, [dispatch]);
  const rollAction = carryOutAction([humanColor, "ROLL", null]);
  const endTurnAction = carryOutAction([humanColor, "END_TURN", null]);

  return (
    <>
      {/* USE Button */}
      <OptionsButton
        disabled={playableDevCardTypes.size === 0 || isPlayingDevCard}
        menuListId="use-menu-list"
        icon={<SimCardIcon />}
        items={useItems}
      >
        Use
      </OptionsButton>

      {/* BUY Button */}
      <OptionsButton
        disabled={buildActionTypes.size === 0 || isPlayingDevCard}
        menuListId="build-menu-list"
        icon={<BuildIcon />}
        items={buildItems}
      >
        Buy
      </OptionsButton>

      {/* TRADE Button */}
      <OptionsButton
        disabled={tradeItems.length === 0 || isPlayingDevCard}
        menuListId="trade-menu-list"
        icon={<AccountBalanceIcon />}
        items={tradeItems}
      >
        Trade
      </OptionsButton>

      {/* END Button */}
      <div className="turn-action-wrapper">
        {dicePreview?.anchor === "turn-action" && (
          <DiceRollPreview
            key={dicePreview.rollId}
            values={dicePreview.values}
            rollerColor={dicePreview.rollerColor}
          />
        )}
        <Button
          className="turn-action-btn"
          disabled={gameState.is_initial_build_phase || isRoadBuilding}
          variant="contained"
          color="secondary"
          startIcon={
            isRoll ? (
              <img src={diceIcon} style={{ width: 24, height: 24 }} alt="roll" />
            ) : isMoveRobber ? (
              <img
                src={robberIcon}
                style={{ width: 24, height: 24 }}
                alt="robber"
              />
            ) : (
              <NavigateNextIcon />
            )
          }
          onClick={
            isDiscard || isPlayingYearOfPlenty || isPlayingMonopoly
              ? handleOpenResourceSelector
              : isMoveRobber
              ? setIsMovingRobber
              : isRoll
              ? rollAction
              : endTurnAction
          }
        >
          {isDiscard
            ? "DISCARD"
            : isMoveRobber
            ? "ROB"
            : isPlayingYearOfPlenty || isPlayingMonopoly
            ? "SELECT"
            : isRoll
            ? "ROLL"
            : "END"}
        </Button>
      </div>
      <ResourceSelector
        open={resourceSelectorOpen}
        onClose={() => {
          setResourceSelectorOpen(false);
          dispatch({ type: ACTIONS.CANCEL_MONOPOLY });
          dispatch({ type: ACTIONS.CANCEL_YEAR_OF_PLENTY });
        }}
        options={isDiscard ? getDiscardOptions() : getValidYearOfPlentyOptions()}
        onSelect={handleResourceSelection}
        mode={
          isDiscard
            ? "discard"
            : isPlayingMonopoly
            ? "monopoly"
            : "yearOfPlenty"
        }
      />
    </>
  );
}

export default function ActionsToolbar({
  isBotThinking,
  replayMode,
}: {
  isBotThinking: boolean;
  replayMode: boolean;
}) {
  const { state, dispatch } = useContext(store);
  const { gameState } = state;
  const [dicePreview, setDicePreview] = useState<DicePreviewState | null>(null);
  const latestAnimatedRollRef = useRef<number>(-1);
  if (gameState === null) {
    console.error("No gameState found...");
    return null;
  }
  const openLeftDrawer = useCallback(() => {
    dispatch({
      type: ACTIONS.SET_LEFT_DRAWER_OPENED,
      data: true,
    });
  }, [dispatch]);

  // NOTE: right-drawer is opened via the fixed blue tab in GameScreen; toolbar should not provide another open control.

  const botsTurn = gameState.bot_colors.includes(gameState.current_color);
  const humanColor = getHumanColor(gameState);
  const showPrompt = botsTurn || Boolean(gameState.winning_color);
  const preserveMobileToolbarSpace = showPrompt && !replayMode;

  useEffect(() => {
    if (!gameState.actions.length) {
      return;
    }

    const latestActionIndex = gameState.actions.length - 1;
    if (latestAnimatedRollRef.current === latestActionIndex) {
      return;
    }

    const latestAction = gameState.actions[latestActionIndex];
    if (latestAction[1] !== "ROLL" || latestAction[2] === null) {
      return;
    }

    latestAnimatedRollRef.current = latestActionIndex;
    setDicePreview({
      values: latestAction[2],
      rollerColor: latestAction[0],
      rollId: latestActionIndex,
      anchor: !showPrompt && !replayMode ? "turn-action" : "toolbar",
    });
  }, [gameState.actions, replayMode, showPrompt]);

  return (
    <>
      <div className="state-summary">
        <div className="hide-on-mobile">
          <Hidden breakpoint={{ size: "md", direction: "up" }}>
            <Button className="open-drawer-btn" onClick={openLeftDrawer}>
              <ChevronLeftIcon />
            </Button>
          </Hidden>
        </div>
        {humanColor && (
          <ResourceCards
            playerState={gameState.player_state}
            playerKey={playerKey(gameState, humanColor)}
            size="large"
          />
        )}
        {/* No right-drawer open control in toolbar (desktop only blue tab in GameScreen handles it). */}
      </div>
      <div
        className="actions-toolbar"
      >
        {dicePreview?.anchor === "toolbar" && (
          <DiceRollPreview
            key={dicePreview.rollId}
            values={dicePreview.values}
            rollerColor={dicePreview.rollerColor}
          />
        )}
        <div
          className={`actions-toolbar-content${
            preserveMobileToolbarSpace ? " mobile-transparent" : ""
          }`}
        >
          {!showPrompt && !replayMode && (
            <div className="play-buttons-group">
              <PlayButtons dicePreview={dicePreview} />
            </div>
          )}
          {showPrompt && (
            <Prompt gameState={gameState} isBotThinking={isBotThinking} />
          )}
          {/* Toolbar intentionally does not duplicate right-drawer content. */}
        </div>
      </div>
    </>
  );
}

type OptionItem = {
  label: string;
  disabled: boolean;
  onClick: (event: MouseEvent | TouchEvent) => void;
};

type OptionsButtonProps = {
  menuListId: string;
  icon: any;
  children: React.ReactNode;
  items: OptionItem[];
  disabled: boolean;
};

function OptionsButton({
  menuListId,
  icon,
  children,
  items,
  disabled,
}: OptionsButtonProps) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLButtonElement>(null);

  const handleToggle = () => {
    setOpen((prevOpen) => !prevOpen);
  };
  const handleClose =
    (onClick?: (event: MouseEvent | TouchEvent) => void) =>
    (event: MouseEvent | TouchEvent) => {
      if (
        anchorRef.current &&
        anchorRef.current.contains(event.target as Node)
      ) {
        return;
      }

      onClick && onClick(event);
      setOpen(false);
    };
  function handleListKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Tab") {
      event.preventDefault();
      setOpen(false);
    }
  }
  // return focus to the button when we transitioned from !open -> open
  const prevOpen = useRef(open);
  useEffect(() => {
    if (prevOpen.current === true && open === false) {
      anchorRef.current && anchorRef.current.focus();
    }

    prevOpen.current = open;
  }, [open]);

  return (
    <React.Fragment>
      <Button
        disabled={disabled}
        ref={anchorRef}
        type="button"
        aria-controls={open ? menuListId : undefined}
        aria-haspopup="true"
        variant="contained"
        color="secondary"
        startIcon={icon}
        onClick={handleToggle}
      >
        {children}
      </Button>
      <Popper
        className="action-popover"
        open={open}
        anchorEl={anchorRef.current}
        role={undefined}
        transition
      >
        {({ TransitionProps, placement }) => (
          <Grow
            {...TransitionProps}
            style={{
              transformOrigin:
                placement === "bottom" ? "center top" : "center bottom",
            }}
          >
            <Paper>
              <ClickAwayListener onClickAway={handleClose()}>
                <MenuList
                  autoFocusItem={open}
                  id={menuListId}
                  onKeyDown={handleListKeyDown}
                >
                  {items.map((item) => (
                    <MenuItem
                      key={item.label}
                      onClick={
                        handleClose(
                          item.onClick
                        ) as unknown as React.MouseEventHandler
                      }
                      disabled={item.disabled}
                    >
                      {item.label}
                    </MenuItem>
                  ))}
                </MenuList>
              </ClickAwayListener>
            </Paper>
          </Grow>
        )}
      </Popper>
    </React.Fragment>
  );
}
