/*
Module: 6. User Interface
Author: Forked
Date: 2025-11-12
Purpose: Provides the adminpage module for the user interface, supporting interaction, presentation, or frontend application wiring.
*/

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Button, CircularProgress } from "@mui/material";

import { getUserStarts, type UserStartRow } from "../utils/apiClient";

import "./AdminPage.scss";

export default function AdminPage() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<UserStartRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRows = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getUserStarts(50);
      setRows(data);
    } catch (err: any) {
      setError(err?.response?.data?.error ?? err?.message ?? "Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRows();
  }, []);

  return (
    <div className="admin-page">
      <div className="admin-shell">
        <div className="admin-header">
          <div>
            <h1>Admin Panel</h1>
            <p>Recent homepage Start clicks captured by the backend.</p>
          </div>
          <div className="admin-actions">
            <Button variant="contained" onClick={() => void loadRows()}>
              Refresh
            </Button>
            <Button variant="outlined" onClick={() => navigate("/")}>
              Home
            </Button>
          </div>
        </div>

        {error && <Alert severity="error">{error}</Alert>}

        <div className="admin-card">
          {loading ? (
            <div className="admin-loading">
              <CircularProgress size={32} />
            </div>
          ) : rows.length === 0 ? (
            <div className="admin-empty">No start analytics rows yet.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>IP</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td>{row.id}</td>
                      <td>{row.ip}</td>
                      <td>{new Date(row.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
