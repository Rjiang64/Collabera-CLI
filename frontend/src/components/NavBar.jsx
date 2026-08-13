// NavBar -- top navigation (MUI AppBar). Role-aware: the Analytics link only
// appears for managers/admins.
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function NavBar() {
  const { user, logout, isManager } = useAuth();

  return (
    <AppBar position="static">
      <Toolbar>
        {/* flexGrow pushes everything after it to the right */}
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          🏦 Bank Management
        </Typography>

        {/* component={Link} makes an MUI button navigate like a router link */}
        <Button color="inherit" component={Link} to="/">Dashboard</Button>
        <Button color="inherit" component={Link} to="/accounts">Accounts</Button>

        {/* ROLE-BASED RENDERING: only managers/admins see Analytics */}
        {isManager && (
          <Button color="inherit" component={Link} to="/analytics">Analytics</Button>
        )}

        <Box sx={{ ml: 2, display: "flex", alignItems: "center" }}>
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.9 }}>
            {user?.email}
          </Typography>
          <Button color="inherit" variant="outlined" onClick={logout}>Logout</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}