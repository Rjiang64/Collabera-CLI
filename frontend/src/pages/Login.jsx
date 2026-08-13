// Login page -- collects email + password and calls auth.login().
// useState holds the input values (controlled components); shows an error alert.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Box, Card, CardContent, TextField, Button, Typography, Alert } from "@mui/material";

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
    <Box sx={{ display: "flex", justifyContent: "center", mt: 8 }}>
      <Card sx={{ width: 380 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>Sign in</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <form onSubmit={handleSubmit}>
            <TextField label="Email" fullWidth margin="normal"
              value={email} onChange={(e) => setEmail(e.target.value)} />
            <TextField label="Password" type="password" fullWidth margin="normal"
              value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button type="submit" variant="contained" fullWidth sx={{ mt: 2 }} disabled={busy}>
              {busy ? "Signing in..." : "Login"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}