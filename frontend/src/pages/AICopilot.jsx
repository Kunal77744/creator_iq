import { useState } from "react";
import AppLayout from "../components/AppLayout.jsx";
import api, { errorMessage } from "../api";

const QUICK_PROMPTS = [
  "What are viewers asking in my YouTube comments? Suggest my next video idea",
  "Give me my channel KPIs, revenue summary, and recommended sponsorship rate",
  "Which of my videos have the highest views and engagement?",
  "How much should I charge for a brand sponsorship?",
];

export default function AICopilot() {
  const [mode, setMode] = useState("agent"); // "agent" | "rag"
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [indexMsg, setIndexMsg] = useState("");
  const [err, setErr] = useState("");

  async function handleIndex() {
    setIndexing(true);
    setErr("");
    setIndexMsg("");
    try {
      const res = await api.post("/api/v1/ai/index");
      setIndexMsg(`Indexed ${res.data.indexed_chunks} content chunk(s) into PostgreSQL pgvector.`);
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setIndexing(false);
    }
  }

  async function sendPrompt(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setErr("");
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q, mode }]);
    setBusy(true);

    try {
      if (mode === "agent") {
        const res = await api.post("/api/v1/ai/agent-chat", { message: q });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: res.data.reply,
            tools: res.data.tools_used || [],
            citations: res.data.citations || [],
          },
        ]);
      } else {
        const res = await api.post("/api/v1/ai/rag-query", { query: q });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: res.data.answer,
            tools: ["pgvector_cosine_retriever"],
            citations: res.data.citations || [],
          },
        ]);
      }
    } catch (e) {
      setErr(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <div className="hello">
        <div>
          <h1>AI Growth Copilot</h1>
          <p className="muted">
            Grounded in your PostgreSQL analytics, revenue ledger, and pgvector RAG index.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <button
            className={mode === "agent" ? "btn-solid" : "btn-link"}
            onClick={() => setMode("agent")}
            type="button"
          >
            Growth Agent
          </button>
          <button
            className={mode === "rag" ? "btn-solid" : "btn-link"}
            onClick={() => setMode("rag")}
            type="button"
          >
            RAG Search
          </button>
          <button
            className="btn-solid"
            onClick={handleIndex}
            disabled={indexing}
            type="button"
            style={{ background: "#0f172a" }}
          >
            {indexing ? "Indexing..." : "Index Content"}
          </button>
        </div>
      </div>

      {err && <div className="error" role="alert">{err}</div>}
      {indexMsg && (
        <div className="card" style={{ borderLeft: "4px solid #22c55e", marginBottom: 16 }}>
          {indexMsg}
        </div>
      )}

      <article className="card" style={{ marginBottom: 16 }}>
        <p className="muted" style={{ marginBottom: 10 }}>Quick Prompts:</p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => sendPrompt(p)}
              style={{
                padding: "6px 12px",
                borderRadius: 999,
                border: "1px solid #cbd5e1",
                background: "#f8fafc",
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              {p}
            </button>
          ))}
        </div>
      </article>

      <article className="card" style={{ minHeight: 320, display: "flex", flexDirection: "column", justifyContent: "space-between", gap: 16 }}>
        <div style={{ display: "grid", gap: 12 }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 16px" }}>
              <h3>Ask CreatorIQ AI</h3>
              <p className="muted" style={{ marginTop: 6 }}>
                Click <strong>Index Content</strong> first if you recently synced new videos, then ask about KPIs, sponsorship pricing, or top content.
              </p>
            </div>
          ) : (
            messages.map((m, i) => (
              <div
                key={i}
                style={{
                  padding: 14,
                  borderRadius: 12,
                  background: m.role === "user" ? "#ede9fe" : "#f8fafc",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: "#475569" }}>
                  {m.role === "user" ? "You" : "CreatorIQ AI"}
                </div>
                <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>{m.text}</div>

                {m.tools && m.tools.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
                    {m.tools.map((t) => (
                      <span
                        key={t}
                        style={{
                          fontSize: 11,
                          padding: "2px 8px",
                          borderRadius: 999,
                          background: "#dbeafe",
                          color: "#1e40af",
                        }}
                      >
                        tool: {t}
                      </span>
                    ))}
                  </div>
                )}

                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: 10, display: "grid", gap: 6 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#475569" }}>Source Citations:</div>
                    {m.citations.map((c, idx) => (
                      <div
                        key={idx}
                        style={{
                          fontSize: 12,
                          padding: "6px 10px",
                          borderRadius: 8,
                          background: "#ffffff",
                          border: "1px solid #e2e8f0",
                        }}
                      >
                        <strong>[{c.platform}{c.chunk_type === "comments" ? " Comments" : ""}] {c.title}</strong> — {(c.views || 0).toLocaleString()} views, {c.engagement_rate}% eng (score {c.score})
                        {c.chunk_type === "comments" && c.chunk_text && (
                          <div style={{ marginTop: 4, color: "#475569" }}>{c.chunk_text}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendPrompt();
          }}
          style={{ display: "flex", gap: 8 }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              mode === "agent"
                ? "Ask the Growth Agent (KPIs, revenue, sponsorship rate, content)..."
                : "Search your indexed videos via pgvector RAG..."
            }
            style={{ flex: 1, padding: "10px 14px", borderRadius: 10, border: "1px solid #cbd5e1" }}
          />
          <button className="btn-solid" disabled={busy} type="submit">
            {busy ? "Thinking..." : "Send"}
          </button>
        </form>
      </article>
    </AppLayout>
  );
}
