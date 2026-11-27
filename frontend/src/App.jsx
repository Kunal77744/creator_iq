// Root application router defining public, protected, and role-restricted routes.
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Profile from "./pages/Profile.jsx";
import Settings from "./pages/Settings.jsx";
import AdminUsers from "./pages/AdminUsers.jsx";
import ComingSoon from "./pages/ComingSoon.jsx";
import SocialAccounts from "./pages/SocialAccounts.jsx";
import ContentAnalytics from "./pages/ContentAnalytics.jsx";
import AudiencePage from "./pages/AudiencePage.jsx";
import RevenuePage from "./pages/RevenuePage.jsx";
import ReportsPage from "./pages/ReportsPage.jsx";
import NotificationsPage from "./pages/NotificationsPage.jsx";
import AICopilot from "./pages/AICopilot.jsx";

// Route guard that requires an authenticated user and optionally checks allowed roles.
function Protected({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  // UI-side authorization. The backend enforces the same rule on every API call.
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

// Route guard for login/register pages that redirects authenticated users to the dashboard.
function GuestOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Navigate to="/dashboard" replace /> : children;
}

// Main App component mapping URL paths to their respective page components.
export default function App() {
  return (
    <Routes>
      {/* Public authentication routes */}
      <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
      <Route path="/register" element={<GuestOnly><Register /></GuestOnly>} />

      {/* Core authenticated workspace routes */}
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="/profile" element={<Protected><Profile /></Protected>} />
      <Route path="/settings" element={<Protected><Settings /></Protected>} />

      {/* Admin-only user management route */}
      <Route path="/admin/users" element={<Protected roles={["admin"]}><AdminUsers /></Protected>} />

      {/* Analytics and AI feature routes */}
      <Route path="/social-accounts" element={<Protected><SocialAccounts /></Protected>} />
      <Route path="/content" element={<Protected><ContentAnalytics /></Protected>} />
      <Route path="/analytics" element={<Protected><ContentAnalytics /></Protected>} />
      <Route path="/audience" element={<Protected><AudiencePage /></Protected>} />
      <Route path="/revenue" element={<Protected><RevenuePage /></Protected>} />
      <Route path="/reports" element={<Protected><ReportsPage /></Protected>} />
      <Route path="/notifications" element={<Protected><NotificationsPage /></Protected>} />
      <Route path="/ai-copilot" element={<Protected><AICopilot /></Protected>} />

      {/* Placeholder route for upcoming modules and fallback redirect */}
      <Route path="/m/:page" element={<Protected><ComingSoon /></Protected>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
