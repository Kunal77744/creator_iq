// Login page: authenticates existing users and redirects to the dashboard.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout.jsx";
import { useAuth } from "../AuthContext.jsx";
import { errorMessage } from "../api";

// Login form component handling email/password sign-in
export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Submit credentials to AuthContext and navigate to dashboard on success
  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout>
      <h1>Welcome back</h1>
      <p className="sub">Log in to see how your content is performing.</p>

      {/* Email and password login form */}
      <form onSubmit={onSubmit} noValidate>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" autoComplete="current-password" required />
        </label>

        {error && <div className="error" role="alert">{error}</div>}

        <button className="btn" disabled={busy || !email || !password}>
          {busy ? "Logging in..." : "Log in"}
        </button>
      </form>

      {/* Link to registration page for new users */}
      <p className="switch">
        New to CreatorIQ? <Link to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}
