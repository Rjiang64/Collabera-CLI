// Login page -- two steps when the account has MFA switched on:
//   step 1 "credentials" -> email + password
//   step 2 "code"        -> the 6-digit code from the authenticator app
// Accounts without MFA never see step 2; login() reports which case it is.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Box, Card, CardContent, TextField, Button, Typography, Alert, Link as MuiLink,
} from "@mui/material";
import { GOLD, NAVY, NAVY_DARK } from "../theme";
// Vite bundles and fingerprints the imported image, so this URL works in dev
// and in the production build alike.
import logo from "../assets/logo.png";

export default function Login() {
  const { login, verifyMfa } = useAuth();
  const navigate = useNavigate(); // redirect after successful login

  const [step, setStep] = useState("credentials"); // "credentials" | "code"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [mfaToken, setMfaToken] = useState(null); // proves step 1 passed
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleCredentials(e) {
    e.preventDefault(); // stop the browser's default full-page submit
    setError("");
    setBusy(true);
    try {
      const result = await login(email, password);
      if (result.mfaRequired) {
        // Password was right, but we are NOT logged in yet -- hold the
        // short-lived token and ask for the code.
        setMfaToken(result.mfaToken);
        setStep("code");
      } else {
        navigate("/"); // no MFA on this account -> straight in
      }
    } catch (err) {
      setError("Invalid email or password"); // 401 lands here
    } finally {
      setBusy(false);
    }
  }

  async function handleCode(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await verifyMfa(mfaToken, code);
      navigate("/"); // second factor accepted -> dashboard
    } catch (err) {
      // The backend is specific here (wrong code / already used / locked out),
      // which is safe because the password step already passed.
      setError(err.response?.data?.detail || "Could not verify that code.");
      setCode("");
    } finally {
      setBusy(false);
    }
  }

  function backToStart() {
    setStep("credentials");
    setMfaToken(null);
    setCode("");
    setError("");
    setPassword("");
  }

  return (
    // Full-height navy backdrop so the login screen reads as its own space.
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        background: `linear-gradient(135deg, ${NAVY} 0%, ${NAVY_DARK} 100%)`,
      }}
    >
      <Box sx={{ width: 400, maxWidth: "100%" }}>
        <Box sx={{ textAlign: "center", color: "#fff", mb: 3 }}>
          <Box
            component="img"
            src={logo}
            alt="SRTRS Bank logo"
            sx={{ height: 88, width: "auto", display: "block", mx: "auto" }}
          />
          <Typography variant="h4" sx={{ mt: 1 }}>SRTRS Bank</Typography>
          <Typography sx={{ opacity: 0.8 }}>
            {step === "credentials"
              ? "Sign in to your account"
              : "Two-factor authentication"}
          </Typography>
        </Box>

        <Card sx={{ borderTop: `4px solid ${GOLD}` }}>
          <CardContent sx={{ p: 3.5 }}>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {step === "credentials" ? (
              <>
                <Typography variant="h5" gutterBottom sx={{ color: NAVY }}>Sign in</Typography>
                <form onSubmit={handleCredentials}>
                  <TextField label="Email" fullWidth margin="normal" autoComplete="username"
                    value={email} onChange={(e) => setEmail(e.target.value)} />
                  <TextField label="Password" type="password" fullWidth margin="normal"
                    autoComplete="current-password"
                    value={password} onChange={(e) => setPassword(e.target.value)} />
                  <Button type="submit" variant="contained" fullWidth
                          sx={{ mt: 2.5, py: 1.2 }} disabled={busy}>
                    {busy ? "Signing in..." : "Login"}
                  </Button>
                </form>
              </>
            ) : (
              <>
                <Typography variant="h5" gutterBottom sx={{ color: NAVY }}>
                  Enter your code
                </Typography>
                <Typography color="text.secondary" sx={{ mb: 1 }}>
                  Open your authenticator app and type the 6-digit code for
                  SRTRS Bank.
                </Typography>

                <form onSubmit={handleCode}>
                  <TextField
                    label="6-digit code"
                    fullWidth
                    margin="normal"
                    value={code}
                    autoFocus
                    // one-time-code lets phones offer the code straight from the
                    // keyboard / autofill instead of making you switch apps
                    autoComplete="one-time-code"
                    inputMode="numeric"
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    slotProps={{
                      htmlInput: {
                        maxLength: 6,
                        style: {
                          fontSize: 30,
                          letterSpacing: 12,
                          textAlign: "center",
                          fontWeight: 700,
                        },
                      },
                    }}
                  />
                  <Button type="submit" variant="contained" fullWidth
                          sx={{ mt: 2, py: 1.2 }} disabled={busy || code.length !== 6}>
                    {busy ? "Verifying..." : "Verify"}
                  </Button>
                </form>

                <Box sx={{ textAlign: "center", mt: 2 }}>
                  <MuiLink component="button" type="button" onClick={backToStart}
                           sx={{ color: "text.secondary" }}>
                    Back to sign in
                  </MuiLink>
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
