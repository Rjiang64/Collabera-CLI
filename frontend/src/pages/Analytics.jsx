// Analytics (Manager Dashboard) -- per-branch stats in an MUI DataGrid.
// Reachable only by managers/admins (guarded in App.jsx); the backend also
// enforces the role (defense in depth).
import { useEffect, useMemo, useState } from "react";
import api from "../api/client";
import {
  Container, Typography, Alert, Card, CardContent, Box, Grid, Chip,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { GOLD, NAVY, NAVY_DARK } from "../theme";
import { money } from "../format";

// Column definitions. The backend sends the branch name and street address
// alongside the totals, so a manager can tell branches apart at a glance
// instead of decoding bare ids.
const columns = [
  { field: "branch_id", headerName: "Branch ID", width: 110 },
  { field: "branch_name", headerName: "Branch", width: 160 },
  { field: "location", headerName: "Location", width: 240, flex: 1, minWidth: 180 },
  { field: "account_count", headerName: "Accounts", width: 130, type: "number" },
  {
    field: "total_balance", headerName: "Total Balance", width: 180, type: "number",
    valueFormatter: (value) => money(value),
  },
];

export default function Analytics() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/v1/analytics/branch-summary")
      .then((res) => {
        // DataGrid requires a unique 'id' per row; branch_id works.
        setRows(res.data.map((r) => ({ id: r.branch_id, ...r })));
      })
      .catch(() => setError("You do not have permission to view analytics."))
      .finally(() => setLoading(false));
  }, []);

  // Roll the per-branch rows up into headline totals for the tiles.
  const totals = useMemo(() => ({
    branches: rows.length,
    accounts: rows.reduce((s, r) => s + Number(r.account_count || 0), 0),
    balance: rows.reduce((s, r) => s + Number(r.total_balance || 0), 0),
  }), [rows]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 0.5, flexWrap: "wrap" }}>
        <Typography variant="h4" sx={{ color: NAVY }}>Branch Analytics</Typography>
        <Chip
          label="Manager view"
          size="small"
          sx={{ fontWeight: 700, color: NAVY_DARK, backgroundColor: GOLD }}
        />
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Accounts and balances by branch location.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Headline tiles above the table */}
      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Tile label="Branches" value={totals.branches} />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Tile label="Total Accounts" value={totals.accounts} />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Tile label="Combined Balance" value={money(totals.balance)} highlight />
        </Grid>
      </Grid>

      {/* DataGrid needs an explicit height from its container */}
      <Card>
        <Box sx={{ height: 440, width: "100%" }}>
          <DataGrid
            rows={rows}
            columns={columns}
            loading={loading}
            pageSizeOptions={[5, 10]}
            initialState={{ pagination: { paginationModel: { pageSize: 5 } } }}
            disableRowSelectionOnClick
            sx={{
              border: "none",
              "& .MuiDataGrid-columnHeaders": { backgroundColor: "#f5f8fb" },
              "& .MuiDataGrid-columnHeaderTitle": { fontWeight: 700, color: NAVY_DARK },
              "& .MuiDataGrid-cell": { borderColor: "#eef2f7" },
            }}
          />
        </Box>
      </Card>
    </Container>
  );
}

// One headline number above the table.
function Tile({ label, value, highlight }) {
  return (
    <Card sx={{ height: "100%", borderBottom: highlight ? `4px solid ${GOLD}` : undefined }}>
      <CardContent sx={{ p: 3 }}>
        <Typography color="text.secondary" sx={{ fontWeight: 600 }}>{label}</Typography>
        <Typography sx={{ fontSize: 30, fontWeight: 800, color: NAVY }}>{value}</Typography>
      </CardContent>
    </Card>
  );
}
