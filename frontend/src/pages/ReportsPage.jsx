import { useState } from "react";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

export default function ReportsPage() {
  const [busy, setBusy] = useState("");
  const [err, setErr] = useState("");

  async function downloadCsv(type) {
    setBusy(type); setErr("");
    try {
      const res = await api.get(`/api/v1/reports/export?report_type=${type}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `creatoriq_${type}_report.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setBusy("");
    }
  }

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>Reports & Export</h1>
          <p className="muted">Generate downloadable Excel-compatible CSV reports and printable PDF summaries.</p>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        <article className="card">
          <h3>Content Analytics Report</h3>
          <p className="muted" style={{ margin: "8px 0 14px" }}>All synced posts, views, likes, comments, shares, and engagement rates.</p>
          <button className="btn-solid" disabled={busy === "analytics"} onClick={() => downloadCsv("analytics")}>
            {busy === "analytics" ? "Exporting..." : "Download CSV / Excel"}
          </button>
        </article>

        <article className="card">
          <h3>Revenue & Sponsorship Report</h3>
          <p className="muted" style={{ margin: "8px 0 14px" }}>Complete ledger of sponsorships, ad revenue, affiliates, and payout status.</p>
          <button className="btn-solid" disabled={busy === "revenue"} onClick={() => downloadCsv("revenue")}>
            {busy === "revenue" ? "Exporting..." : "Download CSV / Excel"}
          </button>
        </article>

        <article className="card">
          <h3>Platform Comparison Report</h3>
          <p className="muted" style={{ margin: "8px 0 14px" }}>Followers, total views, and video counts across connected social platforms.</p>
          <button className="btn-solid" disabled={busy === "platforms"} onClick={() => downloadCsv("platforms")}>
            {busy === "platforms" ? "Exporting..." : "Download CSV / Excel"}
          </button>
        </article>

        <article className="card">
          <h3>PDF Executive Summary</h3>
          <p className="muted" style={{ margin: "8px 0 14px" }}>Print or save the current dashboard & report view directly as a PDF document.</p>
          <button className="btn-solid" onClick={() => window.print()}>
            Print / Save as PDF
          </button>
        </article>
      </div>
    </AppLayout>
  );
}
