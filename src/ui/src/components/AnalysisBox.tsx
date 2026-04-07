/*
Module: 6. User Interface
Author: Forked
Date: 2026-01-30
Purpose: Provides the analysisbox module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { useContext, useState } from "react";
import { Button } from "@mui/material";
import { type MCTSProbabilities, type StateIndex, getMctsAnalysis } from "../utils/apiClient";
import { useParams } from "react-router";

import "./AnalysisBox.scss";
import { store } from "../store";

type AnalysisBoxProps = {
  stateIndex: StateIndex;
  companionAction?: React.ReactNode;
};

export default function AnalysisBox({
  stateIndex,
  companionAction,
}: AnalysisBoxProps) {
  const { gameId } = useParams();
  const { state } = useContext(store);
  const [mctsResults, setMctsResults] = useState<MCTSProbabilities | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const hasResults = !!mctsResults && !loading && !error;

  const handleAnalyzeClick = async () => {
    if (!gameId || !state.gameState || state.gameState.winning_color) return;

    try {
      setLoading(true);
      setError('');
      const result = await getMctsAnalysis(gameId, stateIndex);
      if (result.success) {
        setMctsResults(result.probabilities);
      } else {
        setError(result.error || "Analysis failed");
      }
    } catch (err) {
      console.error("MCTS Analysis failed:", err);
      if (err instanceof Error) {
        setError(err.message);
      } else if (typeof err === "string") {
        setError(err);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-box">
      <div className="analysis-header">
        <h3>Win Probability Analysis</h3>
        <div className="analysis-button-row">
          <Button
            className="analysis-button"
            variant="contained"
            color="primary"
            onClick={handleAnalyzeClick}
            disabled={loading || !!state.gameState?.winning_color}
            fullWidth
            sx={{
              "&.Mui-disabled": {
                backgroundColor: "rgba(255, 255, 255, 0.3)",
                color: "rgba(255, 255, 255, 0.7)",
              },
            }}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </Button>
          {companionAction}
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {hasResults && (
        <div className="probability-bars">
          {Object.entries(mctsResults).map(([color, probability]) => (
            <div key={color} className={`probability-row ${color.toLowerCase()}`}>
              <span className="player-color">
                <span className={`player-dot ${color.toLowerCase()}`} />
                <span className="player-color-label">
                  {color.charAt(0) + color.slice(1).toLowerCase()}
                </span>
              </span>
              <span className="probability-bar">
                <div
                  className="bar-fill"
                  style={{ width: `${probability}%` }}
                />
              </span>
              <span className="probability-value">{probability}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
