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

  // Shared tail of a successful login: save the token so the interceptor can
  // attach it, then load who we are.
  async function completeLogin(accessToken) {
    localStorage.setItem("jwt_token", accessToken);
    const me = await api.get("/api/v1/auth/me");
    setUser(me.data);
    return me.data;
  }

  // LOGIN (step 1): check the password.
  //
  // Returns either:
  //   { mfaRequired: true, mfaToken }  -> caller must collect a 6-digit code
  //                                       and call verifyMfa() with it
  //   { mfaRequired: false, user }     -> logged in, nothing more to do
  //
  // IMPORTANT: when MFA is required we deliberately do NOT store a token or set
  // the user. Until the second factor passes, this person is not logged in.
  async function login(email, password) {
    // IMPORTANT: backend /login uses OAuth2 form format -> send
    // x-www-form-urlencoded with 'username' + 'password' (NOT a JSON body).
    const body = new URLSearchParams();
    body.append("username", email); // backend treats 'username' as the email
    body.append("password", password);

    const res = await api.post("/api/v1/auth/login", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    if (res.data.mfa_required) {
      return { mfaRequired: true, mfaToken: res.data.mfa_token };
    }

    const me = await completeLogin(res.data.access_token);
    return { mfaRequired: false, user: me };
  }

  // LOGIN (step 2): trade the short-lived mfa_token + the code for real tokens.
  async function verifyMfa(mfaToken, code) {
    const res = await api.post("/api/v1/auth/mfa/verify", {
      mfa_token: mfaToken,
      code,
    });
    return completeLogin(res.data.access_token);
  }

  // LOGOUT: forget the token and clear the user.
  function logout() {
    localStorage.removeItem("jwt_token");
    setUser(null);
  }

  // Re-read /me after something changes server-side (e.g. MFA was just turned
  // on), so the UI reflects it without a full page reload.
  async function refreshUser() {
    const me = await api.get("/api/v1/auth/me");
    setUser(me.data);
    return me.data;
  }

  // Derived role helpers so views can render conditionally.
  const roles = user?.roles || [];
  const isStaff = roles.some((r) => ["TELLER", "BRANCH_MANAGER", "ADMIN"].includes(r));
  const isManager = roles.some((r) => ["BRANCH_MANAGER", "ADMIN"].includes(r));

  return (
    <AuthContext.Provider
      value={{ user, loading, login, verifyMfa, logout, refreshUser, isStaff, isManager }}
    >
      {children}
    </AuthContext.Provider>
  );
}
