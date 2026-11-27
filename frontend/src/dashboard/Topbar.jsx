// Global top navigation bar with search, date-range selector, AI trigger, notifications, and logout.
import { useNavigate } from "react-router-dom";
import { Icon } from "./Icons";
import { useDateRange } from "./DateRangeContext";

// Renders the sticky topbar and derives user avatar initials from the user's name.
export default function Topbar({ user, onLogout, onOpenAI }) {
  const navigate = useNavigate();
  const { days, setDays } = useDateRange();
  const initials = user.name.split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();
  return (
    <header className="tb">
      {/* Global search input */}
      <label className="tb-search">
        <Icon name="search" />
        <input type="search" placeholder="Search content, analytics, reports..." aria-label="Search" />
      </label>

      {/* Right-aligned controls: date range, AI button, notifications, user profile, logout */}
      <div className="tb-right">
        <label className="tb-range">
          <Icon name="calendar" />
          <select aria-label="Date range" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
          </select>
        </label>

        {onOpenAI && (
          <button type="button" className="btn-ai" onClick={onOpenAI}>
            Ask AI
          </button>
        )}

        <button className="icon-btn" aria-label="Notifications" onClick={() => navigate("/notifications")}>
          <Icon name="bell" />
          <span className="dot" />
        </button>

        <div className="tb-user">
          <span className="avatar">{initials}</span>
          <span className="tb-name">
            <strong>{user.name}</strong>
            <small>{user.role_label}</small>
          </span>
        </div>

        <button className="icon-btn" onClick={onLogout} aria-label="Log out" title="Log out">
          <Icon name="logout" />
        </button>
      </div>
    </header>
  );
}
