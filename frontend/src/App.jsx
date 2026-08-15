// App -- defines the routes (which URL shows which page) and the nav bar.
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import NavBar from "./components/NavBar";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Analytics from "./pages/Analytics";
import Security from "./pages/Security";

export default function App() {
  const { user } = useAuth();

  return (
    <>
      {/* Only show the nav bar once logged in */}
      {user && <NavBar />}

      <Routes>
        {/* Public route */}
        <Route path="/login" element={<Login />} />

        {/* Protected routes: ProtectedRoute redirects to /login if not signed in */}
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/accounts" element={<ProtectedRoute><Accounts /></ProtectedRoute>} />
        <Route path="/security" element={<ProtectedRoute><Security /></ProtectedRoute>} />

        {/* Analytics also requires a manager/admin ROLE */}
        <Route path="/analytics" element={
          <ProtectedRoute roles={["BRANCH_MANAGER", "ADMIN"]}>
            <Analytics />
          </ProtectedRoute>
        } />

        {/* Any unknown URL redirects home */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}
