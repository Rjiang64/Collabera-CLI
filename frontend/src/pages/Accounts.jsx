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
  // isStaff covers TELLER, BRANCH_MANAGER and ADMIN -- all three see every
  // account, so every "am I looking at my own money or everyone's?" decision
  // on this page keys off isStaff rather than isManager.
  const { isStaff } = useAuth();

  const [accounts, setAccounts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [form, setForm] = useState({ from_account_id: "", to_account_id: "", amount: "" });
  // Separate state for the teller counter form so typing an amount for a
  // deposit can't overwrite a transfer the user was part-way through filling in.
  const [teller, setTeller] = useState({ account_id: "", amount: "" });
  const [msg, setMsg] = useState(null); // {type, text} for the alert
  const [busy, setBusy] = useState(false);
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

  // TELLER-ONLY COUNTER OPERATIONS.
  // The backend gates both routes with require_roles("TELLER","BRANCH_MANAGER",
  // "ADMIN"), so a customer calling them gets a 403 regardless of what the UI
  // shows. Hiding the panel is a convenience, NOT the security boundary.
  //
  // NOTE: like the transfer route, these endpoints read 'amount' as a QUERY
  // PARAM rather than a JSON body -- hence params + a null body.
  async function handleCounterOp(kind) {
    setMsg(null);
    const id = Number(teller.account_id);
    const amount = Number(teller.amount);

    if (!id || !amount || amount <= 0) {
      setMsg({ type: "error", text: "Enter an account ID and an amount greater than zero." });
      return;
    }

    setBusy(true);
    try {
      await api.post(`/api/v1/accounts/${id}/${kind}`, null, { params: { amount } });
      setMsg({
        type: "success",
        text: `${kind === "deposit" ? "Deposited" : "Withdrew"} ${money(amount)} ${
          kind === "deposit" ? "into" : "from"
        } account #${id}.`,
      });
      setTeller({ account_id: "", amount: "" });
      load(); // refresh balances + history so the change is visible immediately
    } catch (err) {
      // The backend returns a specific 400 for "check account id and amount"
      // and for insufficient funds -- surface it rather than a generic message.
      const detail = err.response?.data?.detail;
      setMsg({
        type: "error",
        text: typeof detail === "string" ? detail : `${kind} failed.`,
      });
    } finally {
      setBusy(false);
    }
  }

  const heading = isStaff ? "All Accounts" : "My Accounts";

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 0.5, flexWrap: "wrap" }}>
        <Typography variant="h4" sx={{ color: NAVY }}>{heading}</Typography>
        {/* Make it explicit that staff are looking at everyone's accounts */}
        {isStaff && (
          <Chip
            label="Staff view"
            size="small"
            sx={{ fontWeight: 700, color: NAVY_DARK, backgroundColor: GOLD }}
          />
        )}
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {isStaff
          ? "Every account across all branches."
          : "Your balances, transfers, and history."}
      </Typography>

      {/* One page-level alert shared by the teller counter and the transfer
          form. It lives here rather than inside either card so a teller's
          deposit confirmation doesn't appear under the "Transfer Money"
          heading, which would read as the wrong action having succeeded. */}
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}

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
                {/* Staff are looking at other people's accounts, so show whose */}
                {isStaff && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Customer #{acc.customer_id}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* ---- Teller counter operations: deposit / withdraw on ANY account ----
           Only rendered for staff. The real enforcement is server-side; this
           just keeps the controls out of a customer's way. */}
      {isStaff && (
        <Card sx={{ mt: 4, borderTop: `4px solid ${GOLD}` }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexWrap: "wrap" }}>
              <Typography variant="h5" sx={{ color: NAVY }}>Teller Counter</Typography>
              <Chip
                label="Staff only"
                size="small"
                sx={{ fontWeight: 700, color: NAVY_DARK, backgroundColor: GOLD }}
              />
            </Box>
            <Typography color="text.secondary" sx={{ mt: 0.5 }}>
              Take a deposit or pay out a withdrawal on a customer's account.
            </Typography>

            <Box
              component="form"
              onSubmit={(e) => e.preventDefault()}
              sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 2, alignItems: "center" }}
            >
              <TextField
                size="small" label="Account ID" value={teller.account_id} inputMode="numeric"
                onChange={(e) =>
                  setTeller({ ...teller, account_id: e.target.value.replace(/\D/g, "") })
                }
              />
              <TextField
                size="small" label="Amount" value={teller.amount} inputMode="decimal"
                onChange={(e) => setTeller({ ...teller, amount: e.target.value })}
              />
              <Button
                variant="contained" disabled={busy}
                onClick={() => handleCounterOp("deposit")}
              >
                {busy ? "Working..." : "Deposit"}
              </Button>
              <Button
                variant="outlined" disabled={busy}
                onClick={() => handleCounterOp("withdraw")}
              >
                Withdraw
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Transfer form */}
      <Card sx={{ mt: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ color: NAVY }}>Transfer Money</Typography>
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
