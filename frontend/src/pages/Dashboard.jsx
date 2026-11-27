// Main Dashboard page: routes to role-specific views and provides the creator analytics & onboarding workspace.
import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { useNavigate } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import AIGrowthBrief from "../components/AIGrowthBrief.jsx";
import { useDateRange } from "../dashboard/DateRangeContext.jsx";
import { Icon, PlatformBadge } from "../dashboard/Icons.jsx";
import { AdminDashboard, AgencyDashboard, MarketingDashboard } from "../dashboard/RoleDashboards.jsx";
import {
  Audience,
  ContentPerformance,
  FollowerGrowth,
  KpiRow,
  Revenue,
  TopPosts,
} from "../dashboard/Widgets.jsx";

const PLATFORMS = ["All Platforms", "YouTube", "Instagram", "LinkedIn"];

// Role-specific subtitle messages shown beneath the greeting
const SUBTITLE = {
  creator: "Here's an overview of your content performance across all platforms.",
  agency: "Here's the combined performance of the creators you manage.",
  marketing_team: "Here's how your campaigns and content are performing.",
  admin: "Here's an overview of everyone using CreatorIQ.",
};

// Creator-specific dashboard with platform filters, onboarding flow, AI brief, and analytics widgets
function CreatorDashboard() {
  const navigate = useNavigate();
  const { days } = useDateRange();
  const [platform, setPlatform] = useState("All Platforms");
  const [posts, setPosts] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loadErr, setLoadErr] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState({ ok: true, text: "" });
  const [onboardPlatform, setOnboardPlatform] = useState("YouTube");
  const [onboardHandle, setOnboardHandle] = useState("");

  const plat = platform === "All Platforms" ? "all" : platform.toLowerCase();

  // Fetch overview KPIs and top posts for the selected platform and date range
  const load = useCallback(() => {
    setLoadErr("");
    api.get(`/api/v1/analytics/overview?platform=${plat}&days=${days}`)
      .then((res) => setOverview(res.data))
      .catch((e) => setLoadErr(errorMessage(e)));
    api.get(`/api/v1/analytics/posts?sort_by=views&order=desc&platform=${plat}&days=${days}`)
      .then((res) => setPosts(res.data))
      .catch((e) => { setPosts([]); setLoadErr(errorMessage(e)); });
  }, [plat, days]);

  useEffect(() => { load(); }, [load]);

  // Handle LinkedIn OAuth redirect callback query parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("linkedin_synced") === "true") {
      setSyncMsg({ ok: true, text: "LinkedIn profile connected successfully!" });
      setPlatform("LinkedIn");
      window.history.replaceState({}, document.title, window.location.pathname);
      load();
    } else if (params.get("linkedin_error")) {
      setSyncMsg({ ok: false, text: "LinkedIn: " + params.get("linkedin_error") });
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [load]);

  // Prompt for YouTube channel handle and sync channel data
  const handleSync = async () => {
    const h = window.prompt("Enter YouTube channel handle (e.g. @chaiaurcode) or channel ID (UC...):", overview?.channel_name || "");
    if (!h) return;
    setSyncing(true);
    try {
      const res = await api.post("/api/v1/analytics/youtube/sync", { channel_handle: h.trim() });
      setSyncMsg({ ok: true, text: res.data.message });
      load();
    } catch (err) {
      setSyncMsg({ ok: false, text: errorMessage(err) });
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg({ ok: true, text: "" }), 8000);
    }
  };

  // Prompt for Instagram username and sync profile data
  const handleInstagramSync = async () => {
    const u = window.prompt("Enter Instagram username (e.g. hiteshchoudharyofficial):", "hiteshchoudharyofficial");
    if (!u) return;
    setSyncing(true);
    try {
      const res = await api.post("/api/v1/analytics/instagram/sync", { username: u.trim() });
      setSyncMsg({ ok: true, text: res.data.message });
      load();
    } catch (err) {
      setSyncMsg({ ok: false, text: errorMessage(err) });
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg({ ok: true, text: "" }), 8000);
    }
  };

  // Start LinkedIn OAuth login flow by redirecting to the provider's auth URL
  const handleLinkedInConnect = async () => {
    const token = localStorage.getItem("creatoriq_token");
    if (!token) return;
    try {
      const res = await api.get(`/api/v1/auth/linkedin/login?token=${token}`);
      if (res.data?.auth_url) {
        window.location.href = res.data.auth_url;
      }
    } catch (err) {
      setSyncMsg({ ok: false, text: errorMessage(err) });
    }
  };

  // Submit handler for the first-time onboarding platform connection form
  const handleOnboardSync = async (e) => {
    e.preventDefault();
    if (onboardPlatform === "LinkedIn") {
      return handleLinkedInConnect();
    }
    const h = onboardHandle.trim();
    if (!h) return;
    setSyncing(true);
    try {
      const endpoint =
        onboardPlatform === "Instagram"
          ? "/api/v1/analytics/instagram/sync"
          : "/api/v1/analytics/youtube/sync";
      const payload = onboardPlatform === "Instagram" ? { username: h } : { channel_handle: h };
      const res = await api.post(endpoint, payload);
      setSyncMsg({ ok: true, text: res.data.message || `${onboardPlatform} synced!` });
      setOnboardHandle("");
      load();
    } catch (err) {
      setSyncMsg({ ok: false, text: errorMessage(err) });
    } finally {
      setSyncing(false);
    }
  };

  // Show loading placeholder while initial overview data is being fetched
  if (overview === null && !loadErr) {
    return <article className="card" style={{ padding: 24 }}><p className="muted">Loading your CreatorIQ workspace...</p></article>;
  }

  // Show onboarding card when the creator has not connected any social platform yet
  if (overview && !overview.connected) {
    return (
      <section className="card" style={{ padding: 28, maxWidth: 680, margin: "12px auto" }}>
        <span className="ai-badge">Getting Started</span>
        <h2 style={{ margin: "10px 0 6px" }}>Connect Your First Platform</h2>
        <p className="muted" style={{ marginBottom: 18 }}>
          Choose a social media platform to sync your real analytics, audience growth, and AI insights.
        </p>

        <div className="chips" style={{ marginBottom: 16 }}>
          {["YouTube", "Instagram", "LinkedIn"].map((p) => (
            <button
              key={p}
              type="button"
              className={"chip" + (onboardPlatform === p ? " on" : "")}
              onClick={() => setOnboardPlatform(p)}
            >
              <PlatformBadge name={p} size={18} />
              {p}
            </button>
          ))}
        </div>

        <form onSubmit={handleOnboardSync} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {onboardPlatform !== "LinkedIn" && (
            <input
              value={onboardHandle}
              onChange={(e) => setOnboardHandle(e.target.value)}
              placeholder={
                onboardPlatform === "Instagram"
                  ? "Enter Instagram username (e.g. hiteshchoudharyofficial)"
                  : "Enter YouTube handle (e.g. @chaiaurcode)"
              }
              required
              style={{ flex: 1, minWidth: 220, padding: "10px 14px", borderRadius: 10, border: "1px solid #cbd5e1" }}
            />
          )}
          <button type="submit" className="btn-solid" disabled={syncing}>
            {syncing ? "Syncing..." : onboardPlatform === "LinkedIn" ? "Connect LinkedIn" : `Sync ${onboardPlatform}`}
          </button>
        </form>

        {syncMsg.text && (
          <p className="sample-note" style={{ marginTop: 12, color: syncMsg.ok ? "#15803d" : "#b91c1c" }}>
            {syncMsg.text}
          </p>
        )}
      </section>
    );
  }

  // Build platform filter chips from the creator's connected accounts
  const connectedNames = (overview?.platforms || []).map((p) => {
    const n = (p.platform || "").toLowerCase();
    if (n === "youtube") return "YouTube";
    if (n === "instagram") return "Instagram";
    if (n === "linkedin") return "LinkedIn";
    return n;
  });
  const filterTabs = connectedNames.length > 1 ? ["All Platforms", ...connectedNames] : connectedNames;

  return (
    <>
      {/* Platform filter chips and account sync navigation button */}
      <div className="toolbar-split">
        <div className="chips" role="group" aria-label="Platform filter">
          {filterTabs.map((p) => (
            <button key={p} className={"chip" + (platform === p ? " on" : "")} aria-pressed={platform === p} onClick={() => setPlatform(p)}>
              {p !== "All Platforms" && <PlatformBadge name={p} size={18} />}
              {p}
            </button>
          ))}
        </div>
        <div className="chips actions" role="group" aria-label="Channel sync actions">
          <button className="chip ghost" onClick={() => navigate("/social-accounts")} title="Connect or sync YouTube, Instagram & LinkedIn">
            <Icon name="link" size={14} /> Manage &amp; Sync Accounts
          </button>
        </div>
      </div>

      {/* Sync status bar showing active channel, last sync timestamp, and any errors */}
      <p className="sample-note">
        {overview?.connected ? (
          <>
            <span className={"sample-pill " + (overview.is_live ? "live" : "")}>{overview.is_live ? "Live" : "Synced"}</span>
            Channel: <strong>{overview.channel_name}</strong>
            {overview.last_synced_at && <> • last synced {new Date(overview.last_synced_at + "Z").toLocaleString("en-IN")}</>}
            {" • "}showing last {days} days
          </>
        ) : (
          <>No account connected for this view. Click <strong>Sync YouTube or Instagram</strong> to connect one.</>
        )}
        {syncMsg.text && <span className={"sample-pill " + (syncMsg.ok ? "live" : "")} style={syncMsg.ok ? {} : { background: "#fee2e2", color: "#b91c1c" }}>{syncMsg.ok ? "✓ " : "⚠ "}{syncMsg.text}</span>}
        {loadErr && <span className="sample-pill" style={{ background: "#fee2e2", color: "#b91c1c" }}>⚠ {loadErr}</span>}
      </p>

      {/* AI Growth Brief summary card */}
      <AIGrowthBrief onOpenCopilot={() => navigate("/ai-copilot")} />

      {/* Top KPI summary row */}
      <KpiRow overview={overview} platform={platform} days={days} />

      {/* Primary charts row: follower growth and content performance */}
      <div className="row row-a">
        <FollowerGrowth platform={platform} days={days} />
        <ContentPerformance platform={platform} days={days} />
      </div>

      {/* Secondary row: top posts table alongside audience and revenue widgets */}
      <div className="row row-b">
        <TopPosts posts={posts} />
        <div className="stack">
          <Audience followers={overview?.subscribers} platform={platform} />
          <Revenue overview={overview} days={days} />
        </div>
      </div>
    </>
  );
}

// Map user roles to their corresponding dashboard view component
const VIEWS = { creator: CreatorDashboard, agency: AgencyDashboard, marketing_team: MarketingDashboard, admin: AdminDashboard };

// Top-level Dashboard page rendering a time-based greeting and the user's role view
export default function Dashboard() {
  const { user } = useAuth();
  const View = VIEWS[user.role] || CreatorDashboard;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>{greeting}, {user.name.split(" ")[0]}! <span aria-hidden="true">👋</span></h1>
          <p className="muted">{SUBTITLE[user.role]}</p>
        </div>
      </div>
      <View />
    </AppLayout>
  );
}
