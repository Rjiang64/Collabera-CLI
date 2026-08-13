// ProtectedRoute -- guards a page.
//   not logged in         -> redirect to /login
//   logged in, wrong role -> redirect home
//   logged in, right role -> show the page
// This mirrors the backend's RBAC so we also hide pages the user shouldn't see.
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { CircularProgress, Box } from "@mui/material";

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();

  // While checking for an existing session, show a spinner (avoids a flicker/
  // premature redirect before we know if the user is logged in).
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) return <Navigate to="/login" />; // not logged in

  // Role-restricted page and the user lacks the role -> send home.
  if (roles && !user.roles.some((r) => roles.includes(r))) {
    return <Navigate to="/" />;
  }

  return children; // all checks passed
}