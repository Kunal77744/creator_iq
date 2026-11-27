// Authentication context providing current user state and login/register/logout helpers.
import { createContext, useContext, useEffect, useState } from "react";
import api from "./api";

export const AuthContext = createContext(null);

// Provider component that manages session state and persists JWT tokens in localStorage.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On page refresh, restore the session from the stored token.
  useEffect(() => {
    const token = localStorage.getItem("creatoriq_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/api/v1/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("creatoriq_token"))
      .finally(() => setLoading(false));
  }, []);

  // Authenticate with email and password, store the returned token, and set user state.
  async function login(email, password) {
    // Backend uses the OAuth2 password flow, which expects form-encoded data.
    const form = new URLSearchParams({ username: email, password });
    const res = await api.post("/api/v1/auth/login", form);
    localStorage.setItem("creatoriq_token", res.data.access_token);
    setUser(res.data.user);
  }

  // Create a new user account via the registration endpoint.
  async function register(payload) {
    await api.post("/api/v1/auth/register", payload);
  }

  // Clear the stored token and reset the authenticated user state.
  function logout() {
    localStorage.removeItem("creatoriq_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser: setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// Convenience hook to access authentication state and actions from any component.
export const useAuth = () => useContext(AuthContext);
