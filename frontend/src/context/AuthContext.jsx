// AuthContext -- global authentication state using React's Context API.
//
// WHY Context: the logged-in user + login/logout are needed all over the app
// (nav bar, protected routes, role-based views). Context lets any component read
// this with useAuth() instead of passing props down through every layer.
import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

// Convenience hook: const { user, login } = useAuth()
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // {id, email, roles, customer_id} or null
  const [loading, setLoading] = useState(true); // true while checking for an existing session

  // On first load, if a token exists (e.g. after refresh), fetch the user so the
  // session persists. useEffect with [] runs exactly once.
  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    if (token) {
      api
        .get("/api/v1/auth/me")
        .then((res) => setUser(res.data))
        .catch(() => localStorage.removeItem("jwt_token")) // bad/expired -> drop it
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  // LOGIN: call the backend, store the token, then load the user profile.
  async function login(email, password) {
    // IMPORTANT: backend /login uses OAuth2 form format -> send
    // x-www-form-urlencoded with 'username' + 'password' (NOT a JSON body).
    const body = new URLSearchParams();
    body.append("username", email); // backend treats 'username' as the email
    body.append("password", password);

    const res = await api.post("/api/v1/auth/login", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    // Save the JWT so the interceptor attaches it and the session survives refresh.
    localStorage.setItem("jwt_token", res.data.access_token);

    // Fetch who we are (id, roles, customer_id) and store it.
    const me = await api.get("/api/v1/auth/me");
    setUser(me.data);
    return me.data;
  }

  // LOGOUT: forget the token and clear the user.
  function logout() {
    localStorage.removeItem("jwt_token");
    setUser(null);
  }

  // Derived role helpers so views can render conditionally.
  const roles = user?.roles || [];
  const isStaff = roles.some((r) => ["TELLER", "BRANCH_MANAGER", "ADMIN"].includes(r));
  const isManager = roles.some((r) => ["BRANCH_MANAGER", "ADMIN"].includes(r));

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isStaff, isManager }}>
      {children}
    </AuthContext.Provider>
  );
}
