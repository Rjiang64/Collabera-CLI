// NavBar -- top navigation (MUI AppBar). Role-aware: the Analytics link only
// appears for managers/admins.
import { AppBar, Toolbar, Typography, Button, Box, Chip } from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { GOLD, NAVY, NAVY_DARK } from "../theme";
// Importing the image (rather than hard-coding a path) lets Vite fingerprint
// and bundle it, so the URL stays correct in both dev and a production build.
import logo from "../assets/logo.png";

export default function NavBar() {
  const { user, logout, isManager } = useAuth();
  const { pathname } = useLocation(); // so we can highlight the current page

  // Shared look for a nav link; the active page gets a gold underline.
  const linkSx = (to) => ({
    color: "#fff",
    opacity: pathname === to ? 1 : 0.78,
    borderRadius: 0,
    px: 2,
    borderBottom: "3px solid",
    borderColor: pathname === to ? GOLD : "transparent",
    "&:hover": { opacity: 1, backgroundColor: "rgba(255,255,255,0.08)" },
  });

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        background: `linear-gradient(90deg, ${NAVY_DARK}, ${NAVY})`,
        borderBottom: `3px solid ${GOLD}`,
      }}
    >
      <Toolbar sx={{ gap: 1 }}>
        {/* flexGrow pushes everything after it to the right */}
        <Box sx={{ flexGrow: 1, display: "flex", alignItems: "center", gap: 1.25 }}>
          <Box
            component="img"
            src={logo}
            alt="SRTRS Bank logo"
            sx={{ height: 36, width: "auto", display: "block" }}
          />
          <Typography variant="h6" sx={{ letterSpacing: "-0.3px" }}>
            SRTRS Bank
          </Typography>
        </Box>

        {/* component={Link} makes an MUI button navigate like a router link */}
        <Button component={Link} to="/" sx={linkSx("/")}>Dashboard</Button>
        <Button component={Link} to="/accounts" sx={linkSx("/accounts")}>
          {/* Managers/admins see every customer's account, not just their own */}
          {isManager ? "All Accounts" : "My Accounts"}
        </Button>

        {/* ROLE-BASED RENDERING: only managers/admins see Analytics */}
        {isManager && (
          <Button component={Link} to="/analytics" sx={linkSx("/analytics")}>
            Analytics
          </Button>
        )}

        <Box sx={{ ml: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
          <Box sx={{ textAlign: "right", display: { xs: "none", md: "block" } }}>
            <Typography variant="body2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
              {user?.email}
            </Typography>
            {/* Show the role so it's obvious which view you're looking at */}
            <Chip
              label={(user?.roles || []).join(" · ") || "USER"}
              size="small"
              sx={{
                height: 18,
                fontSize: 10,
                fontWeight: 700,
                color: NAVY_DARK,
                backgroundColor: GOLD,
              }}
            />
          </Box>
          <Button
            onClick={logout}
            variant="outlined"
            sx={{
              color: "#fff",
              borderColor: "rgba(255,255,255,0.45)",
              "&:hover": { borderColor: "#fff", backgroundColor: "rgba(255,255,255,0.08)" },
            }}
          >
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
