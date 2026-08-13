// Accounts (Customer Portal) -- balances, a transfer form, and history.
// Shows useEffect (load on mount), useState (form + data), and secured API calls.
import { useEffect, useState } from "react";
import api from "../api/client";
import {
  Container, Typography, Grid, Card, CardContent, Box, TextField, Button,
  Alert, Table, TableHead, TableRow, TableCell, TableBody, TableContainer, Paper,
} from "@mui/material";

export default function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [form, setForm] = useState({ from_account_id: "", to_account_id: "", amount: "" });
  const [msg, setMsg] = useState(null); // {type, text} for the alert

  // Load accounts + transactions. The interceptor attaches the JWT; the backend
  // already filters these to the logged-in customer's OWN data.
  async function load() {
    const a = await api.get("/api/v1/accounts");
    setAccounts(a.data);
    const t = await api.get("/api/v1/transactions");
    setTxns(t.data);
  }

  // Runs once when the page first renders -> initial data load.
  useEffect(() => { load(); }, []);

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

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>My Accounts</Typography>

      {/* Balance cards -- responsive: 1/row on phones, up to 3/row on desktop */}
      <Grid container spacing={2}>
        {accounts.map((acc) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={acc.id}>
            <Card><CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                {acc.account_type} · Account #{acc.id}
              </Typography>
              <Typography variant="h5">${Number(acc.balance).toLocaleString()}</Typography>
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>

      {/* Transfer form */}
      <Typography variant="h5" sx={{ mt: 4 }}>Transfer Money</Typography>
      {msg && <Alert severity={msg.type} sx={{ my: 2 }}>{msg.text}</Alert>}
      <Box component="form" onSubmit={handleTransfer}
           sx={{ display: "flex", gap: 2, flexWrap: "wrap", my: 2 }}>
        <TextField label="From account ID" value={form.from_account_id}
          onChange={(e) => setForm({ ...form, from_account_id: e.target.value })} />
        <TextField label="To account ID" value={form.to_account_id}
          onChange={(e) => setForm({ ...form, to_account_id: e.target.value })} />
        <TextField label="Amount" value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })} />
        <Button type="submit" variant="contained">Send</Button>
      </Box>

      {/* Transaction history table */}
      <Typography variant="h5" sx={{ mt: 4, mb: 1 }}>Transaction History</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell><TableCell>Type</TableCell>
              <TableCell>From</TableCell><TableCell>To</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {txns.map((t) => (
              <TableRow key={t.id}>
                <TableCell>{t.id}</TableCell>
                <TableCell>{t.type}</TableCell>
                <TableCell>{t.from_account_id ?? "-"}</TableCell>
                <TableCell>{t.to_account_id ?? "-"}</TableCell>
                <TableCell align="right">${Number(t.amount).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
}