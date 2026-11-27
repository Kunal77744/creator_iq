import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

export default function RevenuePage() {
  const [data, setData] = useState(null);
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("sponsorship");
  const [platform, setPlatform] = useState("YouTube");
  const [amount, setAmount] = useState("");
  const [status, setStatus] = useState("paid");
  const [estimateNote, setEstimateNote] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => {
    api.get("/api/v1/revenue")
      .then((r) => setData(r.data))
      .catch((e) => setErr(errorMessage(e)));
  };

  useEffect(() => { load(); }, []);

  async function estimateRate() {
    setErr("");
    try {
      const res = await api.get("/api/v1/ai/sponsorship-estimate");
      const rate = Math.round(res.data.recommended_rate_inr || 0);
      setAmount(String(rate));
      setSource("sponsorship");
      if (!title.trim()) setTitle("AI Estimated Brand Sponsorship");
      setEstimateNote(`AI suggested ₹${rate.toLocaleString()} (${res.data.basis})`);
    } catch (e2) {
      setErr(errorMessage(e2));
    }
  }

  async function addEntry(e) {
    e.preventDefault();
    if (!title.trim() || !amount) return;
    setBusy(true); setErr("");
    try {
      await api.post("/api/v1/revenue", {
        title: title.trim(),
        source,
        platform,
        amount: Number(amount),
        status,
      });
      setTitle(""); setAmount("");
      load();
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy(false);
    }
  }

  async function removeEntry(id) {
    try {
      await api.delete(`/api/v1/revenue/${id}`);
      load();
    } catch (e2) {
      setErr(errorMessage(e2));
    }
  }

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>Revenue & Monetization</h1>
          <p className="muted">Track sponsorships, ad revenue, affiliate earnings, brand collaborations, and payouts.</p>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 20 }}>
        <article className="card">
          <p className="muted">Total Revenue</p>
          <h2>₹{(data?.summary?.total || 0).toLocaleString()}</h2>
        </article>
        <article className="card">
          <p className="muted">Paid</p>
          <h2 style={{ color: "#16a34a" }}>₹{(data?.summary?.paid || 0).toLocaleString()}</h2>
        </article>
        <article className="card">
          <p className="muted">Pending Payouts</p>
          <h2 style={{ color: "#d97706" }}>₹{(data?.summary?.pending || 0).toLocaleString()}</h2>
        </article>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginBottom: 20 }}>
        <article className="card">
          <h3 style={{ marginBottom: 12 }}>Revenue by Source</h3>
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer>
              <BarChart data={data?.breakdown || []}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6d4ae8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h3>Add Revenue / Sponsorship</h3>
            <button type="button" className="btn-ai" onClick={estimateRate}>AI Deal Estimator</button>
          </div>
          {estimateNote && <p className="muted" style={{ marginBottom: 8, color: "#4f46e5" }}>{estimateNote}</p>}
          <form onSubmit={addEntry} style={{ display: "grid", gap: 10 }}>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Campaign or revenue title" required style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1" }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <select value={source} onChange={(e) => setSource(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}>
                <option value="sponsorship">Sponsorship</option>
                <option value="ad_revenue">Ad Revenue</option>
                <option value="brand_collab">Brand Collab</option>
                <option value="affiliate">Affiliate</option>
                <option value="subscription">Subscription</option>
              </select>
              <select value={platform} onChange={(e) => setPlatform(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}>
                <option value="YouTube">YouTube</option>
                <option value="Instagram">Instagram</option>
                <option value="LinkedIn">LinkedIn</option>
              </select>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <input type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Amount (INR)" required style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #cbd5e1" }} />
              <select value={status} onChange={(e) => setStatus(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}>
                <option value="paid">Paid</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <button className="btn-solid" disabled={busy} type="submit">{busy ? "Adding..." : "Add Revenue Entry"}</button>
          </form>
        </article>
      </div>

      <article className="card">
        <h3 style={{ marginBottom: 12 }}>Earnings Ledger</h3>
        <div className="table-wrap">
          <table className="users-table">
            <thead>
              <tr><th>Title</th><th>Source</th><th>Platform</th><th>Amount</th><th>Status</th><th>Date</th><th></th></tr>
            </thead>
            <tbody>
              {(data?.entries || []).map((r) => (
                <tr key={r.revenue_id}>
                  <td><strong>{r.title}</strong></td>
                  <td>{r.source_label}</td>
                  <td>{r.platform}</td>
                  <td>₹{r.amount.toLocaleString()}</td>
                  <td>{r.status}</td>
                  <td>{r.earned_at}</td>
                  <td><button className="btn-link" onClick={() => removeEntry(r.revenue_id)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </AppLayout>
  );
}
