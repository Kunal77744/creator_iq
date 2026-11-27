"""Database-backed tool functions used by the Growth Agent and the MCP server."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Creator, Post, RevenueEntry, SocialAccount
from ..rag.retriever import retrieve_similar_chunks


def get_channel_kpis(db: Session, user_id: int) -> dict:
    """Fetch live channel KPIs (followers, total views, posts, avg engagement) for a user."""
    creator = db.scalar(select(Creator).where(Creator.user_id == user_id))
    if not creator:
        return {"connected": False, "followers": 0, "total_views": 0, "total_posts": 0, "avg_engagement_rate": 0.0}

    accounts = db.scalars(
        select(SocialAccount).where(SocialAccount.creator_id == creator.creator_id, SocialAccount.is_active.is_(True))
    ).all()
    if not accounts:
        return {"connected": False, "followers": 0, "total_views": 0, "total_posts": 0, "avg_engagement_rate": 0.0}

    # Aggregate posts and engagement rates across all active social accounts
    posts = db.scalars(select(Post).where(Post.account_id.in_([a.account_id for a in accounts]))).all()
    rates = [p.analytics.engagement_rate for p in posts if p.analytics and p.analytics.engagement_rate is not None]
    return {
        "connected": True,
        "platforms": [a.platform for a in accounts],
        "followers": sum(a.followers for a in accounts),
        "total_views": sum(a.total_views for a in accounts),
        "total_posts": len(posts),
        "avg_engagement_rate": round(sum(rates) / len(rates), 2) if rates else 0.0,
    }


def get_revenue_summary(db: Session, user_id: int) -> dict:
    """Fetch total, paid, and pending revenue ledger summary for a user."""
    rows = db.scalars(select(RevenueEntry).where(RevenueEntry.user_id == user_id)).all()
    total = sum(r.amount for r in rows)
    paid = sum(r.amount for r in rows if r.status == "paid")
    pending = sum(r.amount for r in rows if r.status != "paid")
    return {
        "total_inr": round(total, 2),
        "paid_inr": round(paid, 2),
        "pending_inr": round(pending, 2),
        "deals_count": len(rows),
    }


def search_creator_content_rag(db: Session, user_id: int, query: str) -> list[dict]:
    """Search creator's indexed content via pgvector cosine similarity."""
    return retrieve_similar_chunks(db, user_id, query, top_k=4)


def calculate_sponsorship_rate(db: Session, user_id: int) -> dict:
    """Estimate fair sponsorship rate in INR from followers, views, and engagement rate."""
    kpis = get_channel_kpis(db, user_id)
    followers = kpis["followers"]
    eng = kpis["avg_engagement_rate"]
    # Base rate scales with followers (minimum 5,000 INR) and is boosted by engagement rate
    base = max(5000.0, followers * 0.15)
    multiplier = 1.0 + (min(eng, 15.0) / 10.0)
    recommended = round(base * multiplier, 2)
    return {
        "recommended_rate_inr": recommended,
        "range_min_inr": round(recommended * 0.8, 2),
        "range_max_inr": round(recommended * 1.25, 2),
        "basis": f"{followers:,} followers at {eng}% avg engagement",
    }
