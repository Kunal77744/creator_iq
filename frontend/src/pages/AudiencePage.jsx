import { useEffect, useState } from "react";
import { Area, AreaChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

export default function AudiencePage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/api/v1/analytics/audience?days=30")
      .then((r) => setData(r.data))
      .catch((e) => setErr(errorMessage(e)));
  }, []);

  const demo = data?.demographics;

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>Audience Analytics</h1>
          <p className="muted">Follower growth trajectory, demographics, top locations, and peak active hours.</p>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}

      {!data ? (
        <article className="card"><p className="muted">Loading audience insights...</p></article>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 20 }}>
            <article className="card">
              <p className="muted">Total Followers</p>
              <h2>{(data.current_followers || 0).toLocaleString()}</h2>
            </article>
            <article className="card">
              <p className="muted">Peak Active Hours</p>
              <h2>{demo?.peak_activity || "18:00 - 21:00"}</h2>
            </article>
            <article className="card">
              <p className="muted">Top Location</p>
              <h2>{demo?.top_locations?.[0]?.[0] || "India"} ({demo?.top_locations?.[0]?.[1] || 48}%)</h2>
            </article>
          </div>

          <article className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ marginBottom: 12 }}>30-Day Follower Growth</h3>
            <div style={{ width: "100%", height: 240 }}>
              <ResponsiveContainer>
                <AreaChart data={data.growth_history || []}>
                  <XAxis dataKey="date" hide={(data.growth_history || []).length > 15} />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="followers" stroke="#6d4ae8" fill="#ede9fe" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          {demo && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
              <article className="card">
                <h3 style={{ marginBottom: 10 }}>Gender Distribution</h3>
                <div style={{ width: "100%", height: 200 }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={demo.gender} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75}>
                        {demo.gender.map((g) => <Cell key={g.name} fill={g.color} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </article>

              <article className="card">
                <h3 style={{ marginBottom: 10 }}>Age Brackets</h3>
                {demo.age_brackets.map(([label, pct]) => (
                  <div key={label} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                      <span>{label}</span><strong>{pct}%</strong>
                    </div>
                    <div style={{ height: 8, background: "#f1f5f9", borderRadius: 4, overflow: "hidden", marginTop: 4 }}>
                      <div style={{ width: `${pct}%`, height: "100%", background: "#6d4ae8" }} />
                    </div>
                  </div>
                ))}
              </article>

              <article className="card">
                <h3 style={{ marginBottom: 10 }}>Geographic Reach</h3>
                {demo.top_locations.map(([loc, pct]) => (
                  <div key={loc} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                      <span>{loc}</span><strong>{pct}%</strong>
                    </div>
                    <div style={{ height: 8, background: "#f1f5f9", borderRadius: 4, overflow: "hidden", marginTop: 4 }}>
                      <div style={{ width: `${pct}%`, height: "100%", background: "#22c55e" }} />
                    </div>
                  </div>
                ))}
              </article>
            </div>
          )}
        </>
      )}
    </AppLayout>
  );
}
