// Security -- where a signed-in user turns multi-factor authentication on/off.
//
// Enrollment is deliberately two steps:
//   1. "Set up"  -> server generates a secret and returns a QR to scan
//   2. "Activate"-> user types a code back, proving the phone really holds the
//                   secret. Only then does MFA switch on.
// Without step 2, a mis-scanned QR would lock the user out of their own account.
import { useEffect, useState } from "react";
import {
  Container, Typography, Card, CardContent, Button, Box, TextField,
  Alert, Chip, Divider, CircularProgress,
} from "@mui/material";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { GOLD, NAVY, NAVY_DARK, CREAM } from "../theme";

export default function Security() {
  const { user, refreshUser } = useAuth();

  const [status, setStatus] = useState(null); // {mfa_enabled, enrollment_pending}
  const [setupData, setSetupData] = useState(null); // {secret, qr_data_uri, ...}
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState(null); // {type, text}
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadStatus() {
    const res = await api.get("/api/v1/auth/mfa/status");
    setStatus(res.data);
    return res.data;
  }

  useEffect(() => {
    loadStatus()
      .catch(() => setMsg({ type: "error", text: "Could not load security settings." }))
      .finally(() => setLoading(false));
  }, []);

  // Step 1: ask the server for a fresh secret + QR code.
  async function handleSetup() {
    setMsg(null);
    setBusy(true);
    try {
      const res = await api.post("/api/v1/auth/mfa/setup");
      setSetupData(res.data);
      await loadStatus();
    } catch {
      setMsg({ type: "error", text: "Could not start setup." });
    } finally {
      setBusy(false);
    }
  }

  // Step 2: prove the phone is enrolled, which flips MFA on.
  async function handleActivate(e) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      await api.post("/api/v1/auth/mfa/activate", { code });
      setSetupData(null);
      setCode("");
      await loadStatus();
      await refreshUser(); // so the nav bar badge updates immediately
      setMsg({ type: "success", text: "Multi-factor authentication is now on." });
    } catch (err) {
      setMsg({ type: "error", text: err.response?.data?.detail || "Could not activate." });
    } finally {
      setBusy(false);
    }
  }

  // Turning MFA off also requires a live code -- a stolen session alone
  // must not be enough to strip the second factor off the account.
  async function handleDisable(e) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      await api.post("/api/v1/auth/mfa/disable", { code });
      setCode("");
      await loadStatus();
      await refreshUser();
      setMsg({ type: "success", text: "Multi-factor authentication is off." });
    } catch (err) {
      setMsg({ type: "error", text: err.response?.data?.detail || "Could not disable." });
    } finally {
      setBusy(false);
    }
  }

  const enabled = status?.mfa_enabled;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" sx={{ color: NAVY }}>Security</Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Signed in as {user?.email}
      </Typography>

      {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}
      {loading && <CircularProgress />}

      {!loading && (
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexWrap: "wrap" }}>
              <Typography variant="h6" sx={{ color: NAVY }}>
                Two-factor authentication
              </Typography>
              <Chip
                label={enabled ? "ON" : "OFF"}
                size="small"
                sx={{
                  fontWeight: 700,
                  color: enabled ? NAVY_DARK : "#fff",
                  backgroundColor: enabled ? GOLD : "#9aa7b4",
                }}
              />
            </Box>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Adds a 6-digit code from your phone on top of your password. The
              code is generated on the device itself, so it works even with no
              signal.
            </Typography>

            <Divider sx={{ my: 3 }} />

            {/* ---- Already on: offer to turn it off (code required) ---- */}
            {enabled && (
              <Box component="form" onSubmit={handleDisable}>
                <Typography sx={{ mb: 1 }}>
                  Enter a current code to turn two-factor off.
                </Typography>
                <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
                  <TextField
                    size="small" label="6-digit code" value={code} inputMode="numeric"
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                  <Button type="submit" variant="outlined" color="error"
                          disabled={busy || code.length !== 6}>
                    Turn off
                  </Button>
                </Box>
              </Box>
            )}

            {/* ---- Not on, and no QR on screen yet: start enrollment ---- */}
            {!enabled && !setupData && (
              <Button variant="contained" onClick={handleSetup} disabled={busy}>
                {busy ? "Preparing..." : "Set up two-factor"}
              </Button>
            )}

            {/* ---- QR on screen: scan, then confirm with a code ---- */}
            {!enabled && setupData && (
              <Box>
                <Typography sx={{ fontWeight: 700, color: NAVY, mb: 1 }}>
                  1. Scan this with your authenticator app
                </Typography>
                <Box
                  component="img"
                  src={setupData.qr_data_uri}
                  alt="Two-factor QR code"
                  sx={{
                    width: 220, height: 220, display: "block",
                    p: 1.5, backgroundColor: "#fff",
                    border: "1px solid #e3e9f0", borderRadius: 2,
                  }}
                />

                <Box sx={{ backgroundColor: CREAM, borderRadius: 2, p: 2, mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Can't scan? Enter this key manually:
                  </Typography>
                  <Typography sx={{ fontFamily: "monospace", fontWeight: 700, wordBreak: "break-all" }}>
                    {setupData.secret}
                  </Typography>
                </Box>

                <Typography sx={{ fontWeight: 700, color: NAVY, mt: 3, mb: 1 }}>
                  2. Enter the code it shows
                </Typography>
                <Box component="form" onSubmit={handleActivate}
                     sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
                  <TextField
                    size="small" label="6-digit code" value={code} autoFocus inputMode="numeric"
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                  <Button type="submit" variant="contained" disabled={busy || code.length !== 6}>
                    {busy ? "Checking..." : "Activate"}
                  </Button>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
