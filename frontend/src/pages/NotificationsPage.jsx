import { useEffect, useState } from "react";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

export default function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [err, setErr] = useState("");

  const load = () => {
    api.get("/api/v1/notifications")
      .then((r) => {
        setItems(r.data.items || []);
        setUnread(r.data.unread_count || 0);
      })
      .catch((e) => setErr(errorMessage(e)));
  };

  useEffect(() => { load(); }, []);

  async function markOne(id) {
    await api.patch(`/api/v1/notifications/${id}/read`);
    load();
  }

  async function markAll() {
    await api.post("/api/v1/notifications/read-all");
    load();
  }

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>Notifications & Alerts ({unread} unread)</h1>
          <p className="muted">Performance alerts, engagement spikes, revenue updates, and scheduled report notices.</p>
        </div>
        {unread > 0 && (
          <button className="btn-solid" onClick={markAll}>Mark All as Read</button>
        )}
      </div>

      {err && <div className="error" role="alert">{err}</div>}

      <div style={{ display: "grid", gap: 12 }}>
        {items.map((n) => (
          <article key={n.notification_id} className="card" style={{ borderLeft: n.is_read ? "4px solid #cbd5e1" : "4px solid #6d4ae8", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
            <div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                <strong>{n.title}</strong>
                <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: "#ede9fe", color: "#5b21b6" }}>{n.category}</span>
              </div>
              <p className="muted">{n.message}</p>
            </div>
            {!n.is_read && (
              <button className="btn-link" onClick={() => markOne(n.notification_id)}>Mark read</button>
            )}
          </article>
        ))}
      </div>
    </AppLayout>
  );
}
