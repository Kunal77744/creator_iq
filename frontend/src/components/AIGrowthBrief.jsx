import { useEffect, useState } from "react";
import api from "../api";

export default function AIGrowthBrief({ onOpenCopilot }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/api/v1/ai/insights")
      .then((r) => setData(r.data))
      .catch(() => {});
  }, []);

  if (!data) return null;

  return (
    <section className="ai-brief" aria-label="AI Growth Brief">
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

      <p className="ai-brief-summary">{data.summary}</p>

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
