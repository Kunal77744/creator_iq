from sqlalchemy.orm import Session

from ..llm import generate_ai_text
from .tools import (
    calculate_sponsorship_rate,
    get_channel_kpis,
    get_revenue_summary,
    search_creator_content_rag,
)


def run_growth_agent(db: Session, user_id: int, message: str) -> dict:
    """Tool-calling Creator Growth Agent grounded in live PostgreSQL & pgvector data."""
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

    fallback_reply = "\n\n".join(sections)
    llm_reply = generate_ai_text(
        f"User question: {message}\n\nVerified CreatorIQ tool outputs:\n{fallback_reply}",
        system_prompt="You are CreatorIQ Growth Agent. Answer clearly and concisely using ONLY the verified tool outputs above. Never invent metrics.",
    )
    return {
        "reply": llm_reply or fallback_reply,
        "tools_used": tools_used,
        "citations": citations,
    }
