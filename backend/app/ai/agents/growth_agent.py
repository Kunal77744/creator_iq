from sqlalchemy.orm import Session

from ..llm import call_gemini_with_tools, llm_is_configured
from .tools import (
    calculate_sponsorship_rate,
    get_channel_kpis,
    get_revenue_summary,
    search_creator_content_rag,
)

TOOL_DECLARATIONS = [
    {
        "name": "get_channel_kpis",
        "description": "Fetch live channel KPIs (followers, total views, posts count, avg engagement rate) for the creator.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "get_revenue_summary",
        "description": "Fetch the creator's revenue and sponsorship payout summary (total, paid, pending in INR).",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "calculate_sponsorship_rate",
        "description": "Calculate recommended brand sponsorship deal pricing in INR from live followers and engagement.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
    {
        "name": "search_creator_content_rag",
        "description": "Search the creator's indexed videos and posts via pgvector RAG or SQL ranking.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Search query about creator's videos or performance"}
            },
            "required": ["query"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are CreatorIQ Growth Agent. Use the provided tools to inspect the creator's real PostgreSQL "
    "metrics, revenue, sponsorship valuation, and RAG content before answering. Never invent numbers."
)


def _execute_tool(db: Session, user_id: int, name: str, args: dict, message: str):
    if name == "get_channel_kpis":
        return get_channel_kpis(db, user_id)
    if name == "get_revenue_summary":
        return get_revenue_summary(db, user_id)
    if name == "calculate_sponsorship_rate":
        return calculate_sponsorship_rate(db, user_id)
    if name == "search_creator_content_rag":
        return search_creator_content_rag(db, user_id, str(args.get("query") or message))
    return {"error": f"Unknown tool: {name}"}


def _run_llm_function_calling(db: Session, user_id: int, message: str) -> dict | None:
    if not llm_is_configured():
        return None

    contents: list[dict] = [{"role": "user", "parts": [{"text": message}]}]
    tools_used: list[str] = []
    citations: list[dict] = []

    for _ in range(4):
        parts = call_gemini_with_tools(contents, TOOL_DECLARATIONS, system_prompt=_SYSTEM_PROMPT)
        if not parts:
            return None

        fn_calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if fn_calls:
            contents.append({"role": "model", "parts": parts})
            response_parts: list[dict] = []
            for fc in fn_calls:
                name = fc.get("name", "")
                args = fc.get("args") or {}
                if name and name not in tools_used:
                    tools_used.append(name)
                result = _execute_tool(db, user_id, name, args, message)
                if name == "search_creator_content_rag" and isinstance(result, list):
                    citations = result
                response_parts.append(
                    {"functionResponse": {"name": name, "response": {"result": result}}}
                )
            contents.append({"role": "user", "parts": response_parts})
            continue

        text = "".join(p.get("text", "") for p in parts).strip()
        if text:
            return {
                "reply": text,
                "tools_used": tools_used,
                "citations": citations,
                "source": "llm_function_calling",
            }
        return None

    return None


def run_growth_agent(db: Session, user_id: int, message: str) -> dict:
    """Agentic Creator Growth Agent: Gemini native function calling with rule-based fallback."""
    llm_result = _run_llm_function_calling(db, user_id, message)
    if llm_result is not None:
        return llm_result

    q = message.lower()
    tools_used: list[str] = []
    sections: list[str] = []
    citations: list[dict] = []

    want_kpis = any(w in q for w in ("kpi", "follower", "subscriber", "view", "channel", "overview", "growth", "summary"))
    want_rev = any(w in q for w in ("revenue", "money", "earn", "income", "payout", "summary"))
    want_sponsor = any(w in q for w in ("sponsor", "rate", "price", "brand", "deal", "charge"))
    want_rag = any(w in q for w in ("video", "post", "content", "topic", "engagement", "best", "top", "why"))

    if not (want_kpis or want_rev or want_sponsor or want_rag):
        want_kpis = want_rag = True

    if want_kpis:
        tools_used.append("get_channel_kpis")
        kpis = get_channel_kpis(db, user_id)
        sections.append(
            f"**Channel KPIs:** {kpis['followers']:,} followers, {kpis['total_views']:,} total views, "
            f"{kpis['total_posts']} posts, {kpis['avg_engagement_rate']}% avg engagement."
        )

    if want_rev:
        tools_used.append("get_revenue_summary")
        rev = get_revenue_summary(db, user_id)
        sections.append(
            f"**Revenue Summary:** ₹{rev['total_inr']:,.0f} total across {rev['deals_count']} entries "
            f"(₹{rev['paid_inr']:,.0f} paid, ₹{rev['pending_inr']:,.0f} pending)."
        )

    if want_sponsor:
        tools_used.append("calculate_sponsorship_rate")
        sp = calculate_sponsorship_rate(db, user_id)
        sections.append(
            f"**Recommended Sponsorship Rate:** ₹{sp['recommended_rate_inr']:,.0f} "
            f"(range ₹{sp['range_min_inr']:,.0f} – ₹{sp['range_max_inr']:,.0f}; based on {sp['basis']})."
        )

    if want_rag:
        tools_used.append("search_creator_content_rag")
        hits = search_creator_content_rag(db, user_id, message)
        citations = hits
        if hits:
            top = hits[0]
            sections.append(
                f"**Top Relevant Content:** [{top['platform']}] {top['title']} "
                f"({top['views']:,} views, {top['engagement_rate']}% engagement)."
            )
        else:
            sections.append("**Content Search:** No indexed posts yet — click 'Index Content' to enable RAG search.")

    return {
        "reply": "\n\n".join(sections),
        "tools_used": tools_used,
        "citations": citations,
        "source": "rule_based_fallback",
    }
