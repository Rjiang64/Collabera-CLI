// Accounts -- balances, a transfer form, and transaction history.
// The heading changes with the caller's role: a customer sees "My Accounts",
// a manager/admin sees "All Accounts" (the backend already returns every
// account to staff and only their own to customers).
// Shows useEffect (load on mount), useState (form + data), and secured API calls.
import { useEffect, useState } from "react";
import api from "../api/client";
import {
  Container, Typography, Grid, Card, CardContent, Box, TextField, Button,
  Alert, Table, TableHead, TableRow, TableCell, TableBody, TableContainer,
  Chip, CircularProgress,
} from "@mui/material";
import { useAuth } from "../context/AuthContext";
import { GOLD, NAVY, NAVY_DARK } from "../theme";
import { money } from "../format";

export default function Accounts() {
  const { isManager } = useAuth();

  const [accounts, setAccounts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [form, setForm] = useState({ from_account_id: "", to_account_id: "", amount: "" });
  const [msg, setMsg] = useState(null); // {type, text} for the alert
  const [loading, setLoading] = useState(true);

  // Load accounts + transactions. The interceptor attaches the JWT; the backend
  // already filters these to the logged-in customer's OWN data.
  async function load() {
    const a = await api.get("/api/v1/accounts");
    setAccounts(a.data);
    const t = await api.get("/api/v1/transactions");
    setTxns(t.data);
  }

  // Runs once when the page first renders -> initial data load.
  useEffect(() => {
    load()
      .catch(() => setMsg({ type: "error", text: "Could not load your accounts." }))
      .finally(() => setLoading(false));
  }, []);

  async function handleTransfer(e) {
    e.preventDefault();
    setMsg(null);
    try {
      // NOTE: the backend transfer route reads QUERY PARAMS (not a JSON body),
      // so we pass them via axios 'params' and send a null body.
      await api.post("/api/v1/transactions/transfer", null, {
        params: {
          from_account_id: Number(form.from_account_id),
          to_account_id: Number(form.to_account_id),
          amount: Number(form.amount),
        },
      });
      setMsg({ type: "success", text: "Transfer completed." });
      setForm({ from_account_id: "", to_account_id: "", amount: "" });
      load(); // refresh balances + history
    } catch (err) {
      const detail = err.response?.data?.detail;
      const text = typeof detail === "string" ? detail : detail?.message || "Transfer failed.";
      setMsg({ type: "error", text });
    }
  }

  const heading = isManager ? "All Accounts" : "My Accounts";

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 0.5, flexWrap: "wrap" }}>
        <Typography variant="h4" sx={{ color: NAVY }}>{heading}</Typography>
        {/* Make it explicit that a manager is looking at everyone's accounts */}
        {isManager && (
          <Chip
            label="Manager view"
            size="small"
            sx={{ fontWeight: 700, color: NAVY_DARK, backgroundColor: GOLD }}
          />
        )}
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {isManager
          ? "Every account across all branches."
          : "Your balances, transfers, and history."}
      </Typography>

      {loading && <CircularProgress />}

      {/* Balance cards -- responsive: 1/row on phones, up to 3/row on desktop */}
      <Grid container spacing={2.5}>
        {accounts.map((acc) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={acc.id}>
            <Card sx={{ height: "100%" }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  {acc.account_type} · Account #{acc.id}
                </Typography>
                <Typography sx={{ fontSize: 30, fontWeight: 800, color: NAVY, my: 0.5 }}>
                  {money(acc.balance)}
                </Typography>
                <Typography sx={{ color: GOLD, fontWeight: 700 }}>
                  Branch #{acc.branch_id}
                  {!acc.is_active && " · inactive"}
                </Typography>
                {/* Managers are looking at other people's accounts, so show whose */}
                {isManager && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Customer #{acc.customer_id}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Transfer form */}
      <Card sx={{ mt: 4 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ color: NAVY }}>Transfer Money</Typography>
          {msg && <Alert severity={msg.type} sx={{ my: 2 }}>{msg.text}</Alert>}
          <Box component="form" onSubmit={handleTransfer}
               sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 2, alignItems: "center" }}>
            <TextField size="small" label="From account ID" value={form.from_account_id}
              onChange={(e) => setForm({ ...form, from_account_id: e.target.value })} />
            <TextField size="small" label="To account ID" value={form.to_account_id}
              onChange={(e) => setForm({ ...form, to_account_id: e.target.value })} />
            <TextField size="small" label="Amount" value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })} />
            <Button type="submit" variant="contained" sx={{ py: 1 }}>Send</Button>
          </Box>
        </CardContent>
      </Card>

      {/* Transaction history table */}
      <Card sx={{ mt: 3 }}>
        <CardContent sx={{ p: 3, pb: 1 }}>
          <Typography variant="h5" sx={{ color: NAVY }}>Transaction History</Typography>
        </CardContent>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ "& th": { fontWeight: 700, color: NAVY_DARK, backgroundColor: "#f5f8fb" } }}>
                <TableCell>ID</TableCell><TableCell>Type</TableCell>
                <TableCell>From</TableCell><TableCell>To</TableCell>
                <TableCell align="right">Amount</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {txns.map((t) => (
                <TableRow key={t.id} hover>
                  <TableCell>{t.id}</TableCell>
                  <TableCell>{t.type}</TableCell>
                  <TableCell>{t.from_account_id ?? "-"}</TableCell>
                  <TableCell>{t.to_account_id ?? "-"}</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700, color: NAVY }}>
                    {money(t.amount)}
                  </TableCell>
                </TableRow>
              ))}
              {!loading && txns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} sx={{ color: "text.secondary" }}>
                    No transactions yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Container>
  );
}
