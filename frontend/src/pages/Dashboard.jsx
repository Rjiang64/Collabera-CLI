// Dashboard -- landing page after login. Shows a greeting, one hero card with
// the combined balance, a card per account, and recent activity.
// Managers see every account; customers see only their own (the backend does
// that filtering, so this page just renders whatever /accounts returns).
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Container, Typography, Grid, Card, CardContent, Button, Box,
  TextField, InputAdornment, Chip, Divider, CircularProgress,
} from "@mui/material";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { GOLD, NAVY, NAVY_DARK, CREAM } from "../theme";
import { money, greeting, firstName } from "../format";

export default function Dashboard() {
  // isStaff (teller/manager/admin) all see every account, so the hero total is
  // "all accounts" for any of them -- not just managers.
  const { user, isStaff } = useAuth();
  const navigate = useNavigate();

  const [accounts, setAccounts] = useState([]);
  const [txns, setTxns] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // Load the same two endpoints the Accounts page uses. The JWT interceptor
  // attaches the token, and the backend decides how much data we're allowed.
  useEffect(() => {
    Promise.all([api.get("/api/v1/accounts"), api.get("/api/v1/transactions")])
      .then(([a, t]) => {
        setAccounts(a.data);
        setTxns(t.data);
      })
      .catch(() => {/* leave the empty state; the Accounts page surfaces errors */})
      .finally(() => setLoading(false));
  }, []);

  // Derive the headline numbers from the data we already fetched.
  // useMemo so this only recalculates when accounts/transactions actually change.
  const stats = useMemo(() => {
    const ids = new Set(accounts.map((a) => a.id));
    const total = accounts.reduce((sum, a) => sum + Number(a.balance), 0);

    // Money IN = anything landing in one of these accounts (deposits + transfers in).
    // Money OUT = anything leaving one of them (withdrawals + transfers out).
    let income = 0, spending = 0, monthNet = 0;
    const now = new Date();

    for (const t of txns) {
      const amt = Number(t.amount);
      const inbound = t.to_account_id != null && ids.has(t.to_account_id);
      const outbound = t.from_account_id != null && ids.has(t.from_account_id);
      if (inbound) income += amt;
      if (outbound) spending += amt;

      // Same-calendar-month delta, used for the change badge on the hero card.
      const d = new Date(t.timestamp);
      if (d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()) {
        if (inbound) monthNet += amt;
        if (outbound) monthNet -= amt;
      }
    }

    // Percent change vs. where the balance stood before this month's activity.
    const opening = total - monthNet;
    const pct = opening > 0 ? (monthNet / opening) * 100 : 0;

    return {
      total,
      income,
      spending,
      active: accounts.filter((a) => a.is_active).length,
      pct,
    };
  }, [accounts, txns]);

  // Recent activity, newest first, narrowed by the search box.
  const recent = useMemo(() => {
    const q = search.trim().toLowerCase();
    return [...txns]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .filter((t) =>
        !q ||
        `${t.type} ${t.description || ""} ${t.id} ${t.amount}`.toLowerCase().includes(q)
      )
      .slice(0, 6);
  }, [txns, search]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* ---- Header: greeting on the left, search + action on the right ---- */}
      <Box
        sx={{
          display: "flex", flexWrap: "wrap", gap: 2,
          alignItems: "center", justifyContent: "space-between", mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ color: NAVY }}>
            {greeting()}, {firstName(user)}
          </Typography>
          <Typography color="text.secondary">
            Here's your account overview for today.
          </Typography>
        </Box>

        <Box sx={{ display: "flex", gap: 1.5, alignItems: "center" }}>
          <TextField
            size="small"
            placeholder="Search transactions..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            sx={{ width: { xs: "100%", sm: 280 } }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">🔍</InputAdornment>
                ),
              },
            }}
          />
          <Button
            variant="contained"
            onClick={() => navigate("/accounts")}
            sx={{ whiteSpace: "nowrap", py: 1.1 }}
          >
            + New Transfer
          </Button>
        </Box>
      </Box>

      {/* ---- Hero card: the combined balance across every visible account ---- */}
      <Card
        sx={{
          mb: 3, border: "none", color: "#fff",
          background: `linear-gradient(135deg, ${NAVY} 0%, ${NAVY_DARK} 100%)`,
          borderBottom: `5px solid ${GOLD}`,
        }}
      >
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          <Typography sx={{ opacity: 0.85, fontWeight: 600 }}>
            {isStaff ? "Total Balance (all accounts)" : "Total Balance"}
          </Typography>

          <Typography sx={{ fontSize: { xs: 40, md: 54 }, fontWeight: 800, lineHeight: 1.15 }}>
            {loading ? <CircularProgress size={34} sx={{ color: "#fff", my: 1 }} /> : money(stats.total)}
          </Typography>

          {/* Change badge -- computed from this month's real transactions */}
          {!loading && (
            <Chip
              label={`${stats.pct >= 0 ? "▲" : "▼"} ${Math.abs(stats.pct).toFixed(1)}% this month`}
              size="small"
              sx={{
                mt: 1, fontWeight: 700, color: GOLD,
                backgroundColor: "rgba(255,255,255,0.12)",
                border: `1px solid ${GOLD}`,
              }}
            />
          )}

          {/* Stat row under the balance */}
          <Box sx={{ display: "flex", gap: { xs: 3, md: 6 }, mt: 3, flexWrap: "wrap" }}>
            <Stat label="Income" value={money(stats.income, 0)} />
            <Stat label="Spending" value={money(stats.spending, 0)} />
            <Stat label="Accounts" value={`${stats.active} active`} />
          </Box>
        </CardContent>
      </Card>

      {/* ---- One card per account ---- */}
      <Grid container spacing={2.5}>
        {accounts.map((acc) => (
          <Grid size={{ xs: 12, md: 6 }} key={acc.id}>
            <Card sx={{ height: "100%" }}>
              <CardContent sx={{ p: 3 }}>
                <Typography color="text.secondary" sx={{ fontWeight: 600 }}>
                  {acc.account_type} · #{acc.id}
                </Typography>
                <Typography sx={{ fontSize: 34, fontWeight: 800, color: NAVY, my: 0.5 }}>
                  {money(acc.balance)}
                </Typography>
                <Typography color="text.secondary">Available balance</Typography>
                <Typography sx={{ color: GOLD, fontWeight: 700, mt: 0.5 }}>
                  Branch #{acc.branch_id}
                  {!acc.is_active && " · inactive"}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {!loading && accounts.length === 0 && (
          <Grid size={{ xs: 12 }}>
            <Card><CardContent sx={{ p: 3 }}>
              <Typography color="text.secondary">
                No accounts to show yet.
              </Typography>
            </CardContent></Card>
          </Grid>
        )}
      </Grid>

      {/* ---- Security strip: describes the access control that is actually
           enforced by the backend on every request. ---- */}
      <Card
        sx={{
          mt: 3, backgroundColor: CREAM,
          border: `1px solid ${GOLD}55`,
          display: "flex", alignItems: "center", gap: 2,
          p: 2.5, flexWrap: "wrap",
        }}
      >
        <Box
          sx={{
            width: 48, height: 48, borderRadius: 2, flexShrink: 0,
            backgroundColor: GOLD, display: "grid", placeItems: "center", fontSize: 24,
          }}
        >
          🛡️
        </Box>
        <Box sx={{ flexGrow: 1, minWidth: 220 }}>
          <Typography variant="h6" sx={{ color: NAVY_DARK }}>
            Role-based access control is active
          </Typography>
          <Typography color="text.secondary">
            Every request is checked against your role before the server runs it.
          </Typography>
        </Box>
        <Chip
          label={`Signed in as ${(user?.roles || []).join(" · ") || "USER"}`}
          sx={{ fontWeight: 700, color: NAVY_DARK, backgroundColor: "#fff", border: `1px solid ${GOLD}` }}
        />
      </Card>

      {/* ---- Recent activity (filtered by the search box above) ---- */}
      <Card sx={{ mt: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ color: NAVY, mb: 1 }}>
            Recent Activity
            {search && (
              <Typography component="span" color="text.secondary" sx={{ ml: 1, fontWeight: 400 }}>
                — matching "{search}"
              </Typography>
            )}
          </Typography>

          {recent.length === 0 ? (
            <Typography color="text.secondary">
              {search ? "No transactions match that search." : "No transactions yet."}
            </Typography>
          ) : (
            recent.map((t, i) => (
              <Box key={t.id}>
                {i > 0 && <Divider />}
                <Box sx={{ display: "flex", alignItems: "center", gap: 2, py: 1.5 }}>
                  <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 700, color: NAVY }}>
                      {t.type}
                      <Typography component="span" color="text.secondary" sx={{ fontWeight: 400 }}>
                        {" "}· #{t.id}
                      </Typography>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {t.description || `${t.from_account_id ?? "—"} → ${t.to_account_id ?? "—"}`}
                    </Typography>
                  </Box>
                  <Typography sx={{ fontWeight: 800, color: NAVY, whiteSpace: "nowrap" }}>
                    {money(t.amount)}
                  </Typography>
                </Box>
              </Box>
            ))
          )}

          <Button component={Link} to="/accounts" sx={{ mt: 1, px: 0 }}>
            View all activity →
          </Button>
        </CardContent>
      </Card>
    </Container>
  );
}

// One label/value pair in the hero card's stat row.
function Stat({ label, value }) {
  return (
    <Box>
      <Typography sx={{ opacity: 0.8, fontSize: 14 }}>{label}</Typography>
      <Typography sx={{ fontWeight: 800, fontSize: 20 }}>{value}</Typography>
    </Box>
  );
}
