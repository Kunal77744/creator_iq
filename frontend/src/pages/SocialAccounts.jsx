// Social Media Integrations page: lets creators sync YouTube/Instagram channels and view supported platforms.
import { useEffect, useState } from "react";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

// SocialAccounts page component for connecting and syncing creator social profiles
export default function SocialAccounts() {
  const [ytHandle, setYtHandle] = useState("@chaiaurcode");
  const [igUser, setIgUser] = useState("");
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [summary, setSummary] = useState(null);

  // Fetch current connected platforms summary from analytics overview
  const loadSummary = () => {
    api.get("/api/v1/analytics/overview")
      .then((r) => setSummary(r.data))
      .catch(() => {});
  };

  useEffect(() => { loadSummary(); }, []);

  // Trigger YouTube channel sync by handle or channel ID
  async function handleSyncYT(e) {
    e.preventDefault();
    setErr(""); setMsg(""); setBusy("yt");
    try {
      const res = await api.post("/api/v1/analytics/youtube/sync", { channel_handle: ytHandle });
      setMsg(res.data.message || "YouTube synced!");
      loadSummary();
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy("");
    }
  }

  // Trigger Instagram profile sync by public username
  async function handleSyncIG(e) {
    e.preventDefault();
    setErr(""); setMsg(""); setBusy("ig");
    try {
      const res = await api.post("/api/v1/analytics/instagram/sync", { username: igUser });
      setMsg(res.data.message || "Instagram synced!");
      loadSummary();
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy("");
    }
  }

  // Build status cards for supported social platforms
  const platforms = [
    { name: "YouTube", status: summary?.platforms?.some((p) => p.platform?.toLowerCase() === "youtube") ? "Connected" : "Ready to Sync", color: "#ef4444" },
    { name: "Instagram", status: summary?.platforms?.some((p) => p.platform?.toLowerCase() === "instagram") ? "Connected" : "Ready to Sync", color: "#d946a8" },
    { name: "LinkedIn", status: "OAuth Ready", color: "#2563eb" },
    { name: "X (Twitter)", status: "API Ready", color: "#0f172a" },
    { name: "Facebook", status: "Graph API Ready", color: "#1d4ed8" },
    { name: "TikTok", status: "Connector Ready", color: "#14b8a6" },
  ];

  return (
    <AppLayout>
      {/* Page header */}
      <div className="hello">
        <div>
          <h1>Social Media Integrations</h1>
          <p className="muted">Connect and synchronize multi-platform creator accounts for real-time analytics.</p>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}
      {msg && <div className="card" style={{ borderLeft: "4px solid #22c55e", marginBottom: 16 }}>{msg}</div>}

      {/* Sync forms for YouTube and Instagram */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginBottom: 20 }}>
        <article className="card">
          <h3>YouTube Data API v3 Sync</h3>
          <p className="muted" style={{ marginBottom: 12 }}>Enter a YouTube handle (e.g. @chaiaurcode) to fetch subscribers, views, and recent videos.</p>
          <form onSubmit={handleSyncYT} style={{ display: "flex", gap: 8 }}>
            <input
              value={ytHandle}
              onChange={(e) => setYtHandle(e.target.value)}
              placeholder="@channelhandle"
              style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1" }}
            />
            <button className="btn-solid" disabled={busy === "yt"} type="submit">
              {busy === "yt" ? "Syncing..." : "Sync YouTube"}
            </button>
          </form>
        </article>

        <article className="card">
          <h3>Instagram Profile Sync</h3>
          <p className="muted" style={{ marginBottom: 12 }}>Enter a public Instagram username to fetch follower metrics and posts.</p>
          <form onSubmit={handleSyncIG} style={{ display: "flex", gap: 8 }}>
            <input
              value={igUser}
              onChange={(e) => setIgUser(e.target.value)}
              placeholder="instagram_username"
              style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1" }}
            />
            <button className="btn-solid" disabled={busy === "ig"} type="submit">
              {busy === "ig" ? "Syncing..." : "Sync Instagram"}
            </button>
          </form>
        </article>
      </div>

      {/* Supported platforms status overview */}
      <article className="card">
        <h3 style={{ marginBottom: 12 }}>Supported Platforms</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
          {platforms.map((p) => (
            <div key={p.name} style={{ padding: 14, borderRadius: 10, border: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ color: p.color }}>{p.name}</strong>
              <span style={{ fontSize: 12, padding: "3px 8px", borderRadius: 999, background: "#f1f5f9" }}>{p.status}</span>
            </div>
          ))}
        </div>
      </article>
    </AppLayout>
  );
}
