// Content & Growth Analytics page: shows 30-day views chart, side-by-side post comparison, and AI post analysis.
import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

// ContentAnalytics page component for exploring post metrics and running AI deep-dives
export default function ContentAnalytics() {
  const [posts, setPosts] = useState([]);
  const [perf, setPerf] = useState([]);
  const [platform, setPlatform] = useState("all");
  const [search, setSearch] = useState("");
  const [p1, setP1] = useState("");
  const [p2, setP2] = useState("");
  const [cmp, setCmp] = useState(null);
  const [aiPost, setAiPost] = useState(null);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [err, setErr] = useState("");

  // Fetch posts and 30-day performance series whenever the platform filter changes
  useEffect(() => {
    const q = platform === "all" ? "" : `?platform=${platform}`;
    Promise.all([
      api.get(`/api/v1/analytics/posts${q}`),
      api.get(`/api/v1/analytics/content-performance${q}`),
    ])
      .then(([r1, r2]) => {
        const list = Array.isArray(r1.data) ? r1.data : (r1.data?.posts || []);
        setPosts(list);
        // Pre-select the first two posts for quick side-by-side comparison
        if (list.length >= 2) {
          setP1(String(list[0].post_id));
          setP2(String(list[1].post_id));
        }
        setPerf(r2.data?.Views || []);
      })
      .catch((e) => setErr(errorMessage(e)));
  }, [platform]);

  // Compare two selected posts via the backend comparison endpoint
  async function runCompare() {
    if (!p1 || !p2 || p1 === p2) return;
    setErr("");
    try {
      const res = await api.get(`/api/v1/analytics/posts/compare?post_ids=${p1},${p2}`);
      setCmp(res.data);
    } catch (e) {
      setErr(errorMessage(e));
    }
  }

  // Request a RAG-backed AI analysis and next-idea suggestions for a single post
  async function analyzePost(postId) {
    setAnalyzingId(postId);
    setErr("");
    try {
      const res = await api.post(`/api/v1/ai/analyze-post/${postId}`);
      setAiPost(res.data);
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setAnalyzingId(null);
    }
  }

  // Filter posts client-side by title search query
  const filtered = posts.filter((p) => (p.title || "").toLowerCase().includes(search.toLowerCase()));

  return (
    <AppLayout>
      {/* Page header with platform selector */}
      <div className="hello">
        <div>
          <h1>Content & Growth Analytics</h1>
          <p className="muted">Track content performance, compare posts side-by-side, and monitor engagement trends.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1" }}>
            <option value="all">All Platforms</option>
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}

      {/* 30-day views bar chart */}
      <article className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginBottom: 12 }}>30-Day Content Views Trend</h3>
        <div style={{ width: "100%", height: 240 }}>
          <ResponsiveContainer>
            <BarChart data={perf}>
              <XAxis dataKey="day" hide={perf.length > 15} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#6d4ae8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>

      {/* Side-by-side content comparison widget (shown when at least 2 posts exist) */}
      {posts.length >= 2 && (
        <article className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 10 }}>Content Comparison</h3>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 12 }}>
            <select value={p1} onChange={(e) => setP1(e.target.value)} style={{ flex: 1, minWidth: 200, padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}>
              {posts.map((p) => <option key={p.post_id} value={p.post_id}>{p.title}</option>)}
            </select>
            <span>vs</span>
            <select value={p2} onChange={(e) => setP2(e.target.value)} style={{ flex: 1, minWidth: 200, padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}>
              {posts.map((p) => <option key={p.post_id} value={p.post_id}>{p.title}</option>)}
            </select>
            <button className="btn-solid" onClick={runCompare}>Compare</button>
          </div>
          {cmp && (
            <div style={{ padding: 12, background: "#f8fafc", borderRadius: 8 }}>
              <p><strong>Views Leader:</strong> {cmp.summary.views_leader} (+{cmp.summary.views_difference.toLocaleString()} views)</p>
              <p><strong>Engagement Leader:</strong> {cmp.summary.engagement_leader} (+{cmp.summary.engagement_difference}%)</p>
            </div>
          )}
        </article>
      )}

      {/* Searchable table of published posts with per-row AI analysis button */}
      <article className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, gap: 10, flexWrap: "wrap" }}>
          <h3>Published Content ({filtered.length})</h3>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search content..."
            style={{ padding: "7px 12px", borderRadius: 8, border: "1px solid #cbd5e1", minWidth: 220 }}
          />
        </div>
        <div className="table-wrap">
          <table className="users-table">
            <thead>
              <tr><th>Title</th><th>Platform</th><th>Views</th><th>Likes</th><th>Comments</th><th>Engagement</th><th>AI</th></tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="7" className="muted" style={{ textAlign: "center", padding: 24 }}>
                    No content found. Sync a social channel in Social Accounts to populate real metrics.
                  </td>
                </tr>
              ) : filtered.map((p) => (
                <tr key={p.post_id}>
                  <td><strong>{p.title}</strong></td>
                  <td>{p.platform}</td>
                  <td>{(p.views || 0).toLocaleString()}</td>
                  <td>{(p.likes || 0).toLocaleString()}</td>
                  <td>{(p.comments || 0).toLocaleString()}</td>
                  <td>{p.engagement_rate}%</td>
                  <td>
                    <button
                      type="button"
                      className="btn-link"
                      disabled={analyzingId === p.post_id}
                      onClick={() => analyzePost(p.post_id)}
                    >
                      {analyzingId === p.post_id ? "Analyzing..." : "Analyze with AI"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>

      {/* AI deep-dive result card for the selected post */}
      {aiPost && (
        <article className="ai-brief" style={{ marginTop: 16 }}>
          <div className="ai-brief-head">
            <div>
              <span className="ai-badge">RAG Deep-Dive</span>
              <h3>{aiPost.title}</h3>
            </div>
            <button type="button" className="btn-link" onClick={() => setAiPost(null)}>Dismiss</button>
          </div>
          <p className="ai-brief-summary">{aiPost.analysis}</p>
          {Array.isArray(aiPost.next_ideas) && (
            <ul className="ai-brief-list">
              {aiPost.next_ideas.map((idea, idx) => <li key={idx}>Next Idea: {idea}</li>)}
            </ul>
          )}
        </article>
      )}
    </AppLayout>
  );
}
