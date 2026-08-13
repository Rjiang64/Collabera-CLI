// Login page -- collects email + password and calls auth.login().
// useState holds the input values (controlled components); shows an error alert.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from "@mui/material";
import { GOLD, NAVY, NAVY_DARK } from "../theme";
// Vite bundles and fingerprints the imported image, so this URL works in dev
// and in the production build alike.
import logo from "../assets/logo.png";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate(); // redirect after successful login

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault(); // stop the browser's default full-page submit
    setError("");
    setBusy(true);
    try {
      await login(email, password); // AuthContext handles the API + token
      navigate("/");                // success -> dashboard
    } catch (err) {
      setError("Invalid email or password"); // 401 lands here
    } finally {
      setBusy(false);
    }
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
          <Typography sx={{ opacity: 0.8 }}>Sign in to your account</Typography>
        </Box>

        <Card sx={{ borderTop: `4px solid ${GOLD}` }}>
          <CardContent sx={{ p: 3.5 }}>
            <Typography variant="h5" gutterBottom sx={{ color: NAVY }}>Sign in</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <form onSubmit={handleSubmit}>
              <TextField label="Email" fullWidth margin="normal"
                value={email} onChange={(e) => setEmail(e.target.value)} />
              <TextField label="Password" type="password" fullWidth margin="normal"
                value={password} onChange={(e) => setPassword(e.target.value)} />
              <Button type="submit" variant="contained" fullWidth
                      sx={{ mt: 2.5, py: 1.2 }} disabled={busy}>
                {busy ? "Signing in..." : "Login"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
