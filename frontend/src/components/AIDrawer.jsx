// Slide-over chat drawer for conversing with the CreatorIQ AI Copilot agent.
import { useState } from "react";
import api, { errorMessage } from "../api";

// Modal drawer component that sends user prompts to /api/v1/ai/agent-chat and renders replies.
export default function AIDrawer({ open, onClose }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  if (!open) return null;

  // Submit the user's question to the AI agent endpoint and append the assistant response.
  async function handleSubmit(e) {
    e.preventDefault();
    const q = input.trim();
    if (!q || busy) return;
    setErr("");
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setBusy(true);
    try {
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
    } catch (e2) {
      setErr(errorMessage(e2));
    } finally {
      setBusy(false);
    }
  }

  return (
    <aside className="ai-drawer-backdrop" role="dialog" aria-label="AI Copilot Drawer">
      <div className="ai-drawer">
        {/* Drawer header with agent badge and close button */}
        <header className="ai-drawer-head">
          <div>
            <span className="ai-badge">Live Agent</span>
            <h3>CreatorIQ AI Copilot</h3>
          </div>
          <button type="button" className="btn-link" onClick={onClose} aria-label="Close AI Drawer">
            Close
          </button>
        </header>

        {/* Scrollable conversation history */}
        <div className="ai-drawer-body">
          {messages.length === 0 && (
            <p className="muted">
              Ask about your live KPIs, revenue payouts, sponsorship pricing, or best-performing videos.
            </p>
          )}
          {messages.map((m, idx) => (
            <div key={idx} className={"ai-msg " + (m.role === "user" ? "user" : "bot")}>
              <div className="ai-msg-text">{m.text}</div>
              {m.tools && m.tools.length > 0 && (
                <div className="ai-tools">
                  {m.tools.map((t) => (
                    <span key={t} className="ai-pill">{t}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {err && <div className="error" role="alert">{err}</div>}
        </div>

        {/* Prompt input bar */}
        <form className="ai-drawer-form" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask CreatorIQ AI..."
          />
          <button type="submit" className="btn-ai" disabled={busy}>
            {busy ? "..." : "Send"}
          </button>
        </form>
      </div>
    </aside>
  );
}
