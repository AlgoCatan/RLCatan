import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Checkbox,
  IconButton,
  MenuItem,
  Select,
  Slider,
  Tooltip,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import HelpOutlineRoundedIcon from "@mui/icons-material/HelpOutlineRounded";
import { GridLoader } from "react-spinners";
import {
  createGame,
  logUserStart,
  type MapTemplate,
  type PlayerArchetype,
} from "../utils/apiClient";
import {
  clearAutoGameConfig,
  saveAutoGameConfig,
} from "../utils/autoMode";

import "./HomePage.scss";

const PLAYER_ARCHETYPES: Array<{
  value: PlayerArchetype;
  label: string;
}> = [
  { value: "HUMAN", label: "Human" },
  { value: "FINAL_BOSS", label: "Final Boss" },
  { value: "CATANATRON", label: "Alpha Beta" },
  { value: "PPO_PLAYER", label: "PPO Player" },
  { value: "VALUE_FUNCTION", label: "Value Function Bot" },
  { value: "MCTS_PLAYER", label: "MCTS" },
  { value: "VP_PLAYER", label: "Victory Point Bot" },
  { value: "PLACEMENT_PLAYER", label: "Placement Only Bot" },
  { value: "WEIGHTED_RANDOM", label: "Weighted Random" },
  { value: "RANDOM", label: "Random" },
];

const MAP_TEMPLATES: MapTemplate[] = ["BASE", "MINI", "TOURNAMENT"];
const PLAYER_COLORS = ["RED", "BLUE", "ORANGE", "WHITE"] as const;
const FRIENDLY_ROBBER_SUPPORTED = true;
const FAMILIARITY_OPTIONS = ["HIGH", "MEDIUM", "LOW"] as const;
type FamiliarityLevel = (typeof FAMILIARITY_OPTIONS)[number];

export default function HomePage() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [loading, setLoading] = useState(false);
  const [mapTemplate, setMapTemplate] = useState<MapTemplate>("BASE");
  const [vpsToWin, setVpsToWin] = useState(10);
  const [discardLimit, setDiscardLimit] = useState(7);
  const [friendlyRobber, setFriendlyRobber] = useState(false);
  const [familiarity, setFamiliarity] = useState<FamiliarityLevel>("MEDIUM");
  const [players, setPlayers] = useState<PlayerArchetype[]>([
    "HUMAN",
    "FINAL_BOSS",
  ]);
  const navigate = useNavigate();
  const humanCount = players.filter((player) => player === "HUMAN").length;
  const hasTooManyHumans = humanCount > 1;
  const hasHumanPlayer = humanCount > 0;
  const selectMenuProps = {
    variant: "menu" as const,
    anchorOrigin: {
      vertical: "bottom" as const,
      horizontal: "left" as const,
    },
    transformOrigin: {
      vertical: "top" as const,
      horizontal: "left" as const,
    },
    PaperProps: {
      className: "player-select-menu",
    },
    ...(isMobile
      ? {
          disablePortal: true,
          disableScrollLock: true,
        }
      : {}),
  };

  const handlePlayerChange = (index: number, value: PlayerArchetype) => {
    if (
      value === "HUMAN" &&
      players[index] !== "HUMAN" &&
      humanCount >= 1
    ) {
      return;
    }

    setPlayers((current) =>
      current.map((player, playerIndex) =>
        playerIndex === index ? value : player
      )
    );
  };

  const handleAddPlayer = () => {
    setPlayers((current) =>
      current.length >= 4 ? current : [...current, "WEIGHTED_RANDOM"]
    );
  };

  const handleRemovePlayer = (index: number) => {
    setPlayers((current) =>
      current.length <= 2
        ? current
        : current.filter((_, playerIndex) => playerIndex !== index)
    );
  };

  const handleCreateGame = async () => {
    if (hasTooManyHumans) {
      return;
    }

    clearAutoGameConfig();
    setLoading(true);
    try {
      try {
        await logUserStart();
      } catch (error) {
        console.error("Failed to log start analytics", error);
      }

      const gameId = await createGame({
        players,
        mapTemplate,
        vpsToWin,
        discardLimit,
        friendlyRobber: FRIENDLY_ROBBER_SUPPORTED ? friendlyRobber : false,
        familiarity,
      });
      navigate("/games/" + gameId);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAutoGame = async () => {
    if (hasTooManyHumans || hasHumanPlayer) {
      return;
    }

    const config = {
      players,
      mapTemplate,
      vpsToWin,
      discardLimit,
      friendlyRobber: FRIENDLY_ROBBER_SUPPORTED ? friendlyRobber : false,
      familiarity,
    };

    saveAutoGameConfig(config);
    setLoading(true);
    const gameId = await createGame(config);
    setLoading(false);
    navigate(`/games/${gameId}?auto=1`);
  };

  return (
    <div className="home-page">
      <h1 className="logo">Catan Arena</h1>

      <div className="switchable">
        {!loading ? (
          <>
            <div className="setup-card">
              <div className="control-group">
                <div className="control-header">
                  <span>Map Type</span>
                  <strong>{mapTemplate}</strong>
                </div>
                <div className="map-template-buttons">
                  {MAP_TEMPLATES.map((value) => (
                    <Button
                      key={value}
                      variant="contained"
                      onClick={() => setMapTemplate(value)}
                      className={`choice-button ${
                        mapTemplate === value ? "selected" : ""
                      }`}
                    >
                      {value}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="control-row">
                <div className="control-group compact-control">
                  <div className="control-header">
                    <span>Points to Win</span>
                    <strong>{vpsToWin}</strong>
                  </div>
                  <Slider
                    value={vpsToWin}
                    min={3}
                    max={20}
                    step={1}
                    marks
                    valueLabelDisplay="auto"
                    onChange={(_, value) => setVpsToWin(value as number)}
                  />
                </div>

                <div className="control-group compact-control">
                  <div className="control-header">
                    <span>Card Discard Limit</span>
                    <strong>{discardLimit}</strong>
                  </div>
                  <Slider
                    value={discardLimit}
                    min={5}
                    max={20}
                    step={1}
                    marks
                    valueLabelDisplay="auto"
                    onChange={(_, value) => setDiscardLimit(value as number)}
                  />
                </div>

                <div className="control-group compact-control switch-control">
                  <div className="control-header switch-header">
                    <span className="switch-label-row">
                      <span className="inline-title">
                        Friendly Robber
                        <Tooltip
                          title={
                            FRIENDLY_ROBBER_SUPPORTED
                              ? "Prevent robber placement on opponents with less than 3 actual victory points."
                              : "Friendly Robber is not supported in this fork yet."
                          }
                          arrow
                          enterTouchDelay={0}
                          leaveTouchDelay={3000}
                        >
                          <IconButton
                            size="small"
                            className="help-button"
                            aria-label="Friendly Robber help"
                          >
                            <HelpOutlineRoundedIcon fontSize="inherit" />
                          </IconButton>
                        </Tooltip>
                      </span>
                      <Checkbox
                        className="inline-switch"
                        checked={friendlyRobber}
                        disabled={!FRIENDLY_ROBBER_SUPPORTED}
                        onChange={(event) =>
                          setFriendlyRobber(event.target.checked)
                        }
                      />
                      <span className="switch-status">
                        {FRIENDLY_ROBBER_SUPPORTED
                          ? friendlyRobber
                            ? "On"
                            : "Off"
                          : "Unavailable"}
                      </span>
                    </span>
                  </div>
                  {!FRIENDLY_ROBBER_SUPPORTED && <div className="control-footnote">Not supported in this build.</div>}
                </div>

                <div className="control-group compact-control familiarity-control">
                  <div className="control-header familiarity-header">
                    <span>Familiarity</span>
                    <Select
                      className="familiarity-select"
                      size="small"
                      value={familiarity}
                      MenuProps={selectMenuProps}
                      onChange={(event) =>
                        setFamiliarity(event.target.value as FamiliarityLevel)
                      }
                    >
                      {FAMILIARITY_OPTIONS.map((option) => (
                        <MenuItem key={option} value={option}>
                          {option.charAt(0) + option.slice(1).toLowerCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </div>
                </div>
              </div>

              <div className="control-group">
                <div className="control-header">
                  <span className="players-heading">
                    Players
                    <span className="players-hint">(At most one Human player)</span>
                  </span>
                </div>
                {hasTooManyHumans && (
                  <Alert severity="error" className="players-alert">
                    Only one Human player is allowed.
                  </Alert>
                )}
                <div className="players-list">
                  {players.map((player, index) => (
                    <div className="player-row" key={`${player}-${index}`}>
                      <div className="player-meta">
                        <span className="player-label">Player {index + 1}</span>
                        <span
                          className={`player-color-chip ${PLAYER_COLORS[index].toLowerCase()}`}
                        >
                          {PLAYER_COLORS[index]}
                        </span>
                      </div>
                      <Select
                        className="player-select"
                        size="small"
                        value={player}
                        MenuProps={selectMenuProps}
                        onChange={(event) =>
                          handlePlayerChange(
                            index,
                            event.target.value as PlayerArchetype
                          )
                        }
                      >
                        {PLAYER_ARCHETYPES.map((option) => (
                          <MenuItem
                            key={option.value}
                            value={option.value}
                            disabled={
                              option.value === "HUMAN" &&
                              humanCount >= 1 &&
                              player !== "HUMAN"
                            }
                          >
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                      <Button
                        variant="text"
                        className="remove-player-btn"
                        disabled={players.length <= 2}
                        onClick={() => handleRemovePlayer(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>

                <Button
                  variant="contained"
                  className="add-player-btn"
                  disabled={players.length >= 4}
                  onClick={handleAddPlayer}
                >
                  Add Player ({players.length}/4)
                </Button>
              </div>

              <div className="primary-actions">
                <Button
                  variant="contained"
                  color="primary"
                  className="start-btn"
                  disabled={hasTooManyHumans}
                  onClick={handleCreateGame}
                >
                  Start
                </Button>
              </div>
            </div>
            {!isMobile && (
              <div className="auto-hover-anchor">
                <Button
                  variant="contained"
                  color="primary"
                  className="auto-btn"
                  disabled={hasTooManyHumans || hasHumanPlayer}
                  onClick={handleCreateAutoGame}
                >
                  Auto
                </Button>
              </div>
            )}
          </>
        ) : (
          <GridLoader
            className="loader"
            color="#ffffff"
            size={60}
          />
        )}
      </div>
    </div>
  );
}
