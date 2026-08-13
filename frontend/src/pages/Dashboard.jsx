// Dashboard -- landing page after login. Responsive MUI Grid of cards; the
// Analytics card shows ONLY to managers (role-based rendering).
import { Container, Typography, Grid, Card, CardContent, Button } from "@mui/material";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user, isManager } = useAuth();

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Welcome, {user?.full_name || user?.email}
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Roles: {user?.roles?.join(", ")}
      </Typography>

      {/* Grid: xs=12 (full width on phones), md=6 (half width -> 2 per row on desktop) */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card><CardContent>
            <Typography variant="h6">My Accounts</Typography>
            <Typography color="text.secondary">
              View balances, transaction history, and transfer money.
            </Typography>
            <Button component={Link} to="/accounts" sx={{ mt: 1 }}>Open</Button>
          </CardContent></Card>
        </Grid>

        {/* Only render the Analytics card for managers/admins */}
        {isManager && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card><CardContent>
              <Typography variant="h6">Branch Analytics</Typography>
              <Typography color="text.secondary">
                Branch performance and account distribution.
              </Typography>
              <Button component={Link} to="/analytics" sx={{ mt: 1 }}>Open</Button>
            </CardContent></Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}