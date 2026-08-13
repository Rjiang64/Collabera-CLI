// Analytics (Manager Dashboard) -- per-branch stats in an MUI DataGrid.
// Reachable only by managers/admins (guarded in App.jsx); the backend also
// enforces the role (defense in depth).
import { useEffect, useState } from "react";
import api from "../api/client";
import { Container, Typography, Alert } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";

// Column definitions. valueFormatter formats the balance as money.
const columns = [
  { field: "branch_id", headerName: "Branch ID", width: 130 },
  { field: "account_count", headerName: "Accounts", width: 150 },
  {
    field: "total_balance", headerName: "Total Balance", width: 200,
    valueFormatter: (value) => `$${Number(value).toLocaleString()}`,
  },
];

export default function Analytics() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/v1/analytics/branch-summary")
      .then((res) => {
        // DataGrid requires a unique 'id' per row; branch_id works.
        setRows(res.data.map((r) => ({ id: r.branch_id, ...r })));
      })
      .catch(() => setError("You do not have permission to view analytics."));
  }, []);

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Branch Analytics</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {/* DataGrid needs an explicit height from its container */}
      <div style={{ height: 420, width: "100%" }}>
        <DataGrid rows={rows} columns={columns} pageSizeOptions={[5, 10]} />
      </div>
    </Container>
  );
}