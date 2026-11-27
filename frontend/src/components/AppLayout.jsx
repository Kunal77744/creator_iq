// Authenticated application shell combining Sidebar, Topbar, main content, and AIDrawer.
import { useState } from "react";
import { useAuth } from "../AuthContext.jsx";
import Sidebar from "../dashboard/Sidebar.jsx";
import Topbar from "../dashboard/Topbar.jsx";
import { DateRangeProvider } from "../dashboard/DateRangeContext.jsx";
import AIDrawer from "./AIDrawer.jsx";
import "../dashboard/dashboard.css";

// Wraps authenticated pages with shared navigation, date-range context, and the AI drawer.
export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <DateRangeProvider>
      <div className="dash">
        {/* Role-aware left navigation sidebar */}
        <Sidebar role={user.role} />
        <div className="dash-main">
          {/* Global topbar with date filter, AI trigger, and user menu */}
          <Topbar user={user} onLogout={logout} onOpenAI={() => setAiOpen(true)} />
          <main className="dash-body">{children}</main>
        </div>
        {/* Slide-over AI Copilot chat drawer */}
        <AIDrawer open={aiOpen} onClose={() => setAiOpen(false)} />
      </div>
    </DateRangeProvider>
  );
}
