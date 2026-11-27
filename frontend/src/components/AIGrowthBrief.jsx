// Summary banner displaying AI-generated growth insights on the dashboard.
import { useEffect, useState } from "react";
import api from "../api";

// Fetches insights from /api/v1/ai/insights and optionally triggers the AI Copilot drawer.
export default function AIGrowthBrief({ onOpenCopilot }) {
  const [data, setData] = useState(null);

  // Load AI growth insights once when the component mounts.
  useEffect(() => {
    api.get("/api/v1/ai/insights")
      .then((r) => setData(r.data))
      .catch(() => {});
  }, []);

  if (!data) return null;

  return (
    <section className="ai-brief" aria-label="AI Growth Brief">
      {/* Header with title and optional button to open the AI Copilot */}
      <div className="ai-brief-head">
        <div>
          <span className="ai-badge">CreatorIQ AI</span>
          <h3>AI Growth Brief</h3>
        </div>
        {onOpenCopilot && (
          <button type="button" className="btn-ai" onClick={onOpenCopilot}>
            Ask AI Copilot
          </button>
        )}
      </div>

      {/* High-level AI summary paragraph */}
      <p className="ai-brief-summary">{data.summary}</p>

      {/* Bullet list of individual AI insight items */}
      {Array.isArray(data.insights) && data.insights.length > 0 && (
        <ul className="ai-brief-list">
          {data.insights.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
