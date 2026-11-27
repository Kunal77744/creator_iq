import { useState } from "react";
import { useAuth } from "../AuthContext.jsx";
import Sidebar from "../dashboard/Sidebar.jsx";
import Topbar from "../dashboard/Topbar.jsx";
import { DateRangeProvider } from "../dashboard/DateRangeContext.jsx";
import AIDrawer from "./AIDrawer.jsx";
import "../dashboard/dashboard.css";

export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const [aiOpen, setAiOpen] = useState(false);

  return (
    <DateRangeProvider>
      <div className="dash">
        <Sidebar role={user.role} />
        <div className="dash-main">
          <Topbar user={user} onLogout={logout} onOpenAI={() => setAiOpen(true)} />
          <main className="dash-body">{children}</main>
        </div>
        <AIDrawer open={aiOpen} onClose={() => setAiOpen(false)} />
      </div>
    </DateRangeProvider>
  );
}
