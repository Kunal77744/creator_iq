"""AI Copilot, RAG indexing/querying, growth insights, post analysis, and sponsorship rate endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai.agents.growth_agent import run_growth_agent
from ..ai.agents.tools import calculate_sponsorship_rate, get_channel_kpis, get_revenue_summary
from ..ai.llm import generate_ai_text
from ..ai.rag.ingestion import index_creator_content
from ..ai.rag.retriever import answer_rag_query, retrieve_similar_chunks
from ..core.rate_limit import rate_limit
from ..database import get_db
from ..deps import get_current_user
from ..models import Creator, Post, SocialAccount, User

router = APIRouter(prefix="/ai", tags=["AI Copilot & RAG"])


class RagQueryRequest(BaseModel):
    """Request schema for RAG search/answering."""

    query: str = Field(min_length=1, max_length=1000)

    @field_validator("query")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """Reject whitespace-only queries and trim surrounding spaces."""
        if not v or not v.strip():
            raise ValueError("Query must not be empty")
        return v.strip()


class AgentChatRequest(BaseModel):
    """Request schema for the AI growth agent chat."""

    message: str = Field(min_length=1, max_length=1000)

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """Reject whitespace-only messages and trim surrounding spaces."""
        if not v or not v.strip():
            raise ValueError("Message must not be empty")
        return v.strip()


@router.post("/index", dependencies=[Depends(rate_limit("ai", limit=30, window_seconds=60))])
def index_content(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Index the current creator's posts into vector storage for RAG."""
    count = index_creator_content(db, current_user.user_id)
    return {"status": "ok", "indexed_chunks": count}


@router.post("/rag-query", dependencies=[Depends(rate_limit("ai", limit=30, window_seconds=60))])
def rag_query(body: RagQueryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Answer a question using retrieval-augmented generation over the user's indexed content."""
    return answer_rag_query(db, current_user.user_id, body.query)


@router.post("/agent-chat", dependencies=[Depends(rate_limit("ai", limit=30, window_seconds=60))])
def agent_chat(body: AgentChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Run the multi-tool AI growth agent for a user chat message."""
    return run_growth_agent(db, current_user.user_id, body.message)


@router.get("/insights")
def get_ai_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return an AI Growth Brief grounded in the creator's live KPIs, posts, and revenue."""
    # Fetch live channel KPIs and revenue totals
    kpis = get_channel_kpis(db, current_user.user_id)
    rev = get_revenue_summary(db, current_user.user_id)

    # Return onboarding guidance if no social channel or posts are synced yet
    if not kpis["connected"] or kpis["total_posts"] == 0:
        return {
            "has_data": False,
            "summary": "Connect a YouTube or Instagram channel to unlock live AI Growth Insights.",
            "insights": [
                "Sync your primary channel in Social Accounts to index your content into pgvector.",
                "Track sponsorships and AdSense in Revenue to enable AI deal pricing.",
            ],
            "source": "fallback",
        }

    # Estimate sponsorship rate and ask the LLM for a 2-sentence executive summary
    sp = calculate_sponsorship_rate(db, current_user.user_id)
    prompt = (
        f"Followers: {kpis['followers']:,}, Total Views: {kpis['total_views']:,}, "
        f"Posts: {kpis['total_posts']}, Avg Engagement: {kpis['avg_engagement_rate']}%, "
        f"Total Revenue: ₹{rev['total_inr']:,.0f}, Fair Sponsor Rate: ₹{sp['recommended_rate_inr']:,.0f}."
    )
    llm_summary = generate_ai_text(
        f"Give a 2-sentence executive growth summary for this creator:\n{prompt}",
        system_prompt="You are CreatorIQ AI Growth Strategist. Be concise and specific.",
    )
    # Build deterministic bullet insights as both supporting points and LLM fallback
    insights = [
        f"Channel momentum: {kpis['followers']:,} followers across {', '.join(kpis['platforms'])} with {kpis['avg_engagement_rate']}% avg engagement.",
        f"Monetization benchmark: Recommended sponsorship rate is ₹{sp['recommended_rate_inr']:,.0f} (range ₹{sp['range_min_inr']:,.0f}–₹{sp['range_max_inr']:,.0f}).",
        f"Revenue health: ₹{rev['paid_inr']:,.0f} settled and ₹{rev['pending_inr']:,.0f} pending across {rev['deals_count']} tracked deals.",
    ]
    return {
        "has_data": True,
        "summary": llm_summary or insights[0],
        "insights": insights,
        "recommended_rate_inr": sp["recommended_rate_inr"],
        "source": "llm" if llm_summary else "fallback",
    }


@router.post("/analyze-post/{post_id}")
def analyze_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deep-dive RAG analysis on a specific post owned by the current user."""
    # Verify the current user has a creator profile and owns the requested post
    creator = db.scalar(select(Creator).where(Creator.user_id == current_user.user_id))
    if not creator:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    acc_ids = list(db.scalars(select(SocialAccount.account_id).where(SocialAccount.creator_id == creator.creator_id)).all())
    post = (
        db.scalar(select(Post).where(Post.post_id == post_id, Post.account_id.in_(acc_ids)))
        if acc_ids
        else None
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    # Extract post performance metrics with safe defaults
    a = post.analytics
    views = a.views if a else 0
    likes = a.likes if a else 0
    comments = a.comments if a else 0
    eng = a.engagement_rate if a else 0.0
    title = post.caption or "Untitled"

    # Retrieve related indexed chunks and generate an LLM post analysis (with template fallback)
    related = retrieve_similar_chunks(db, current_user.user_id, title, top_k=3)
    llm_analysis = generate_ai_text(
        f"Analyze why this post performed well and suggest 3 follow-up video titles:\nTitle: {title}\nViews: {views:,}, Likes: {likes:,}, Comments: {comments:,}, Engagement: {eng}%",
        system_prompt="You are CreatorIQ Content Strategist. Keep it practical and concise.",
    )
    analysis = llm_analysis or (
        f"'{title}' achieved {views:,} views with {eng}% engagement ({likes:,} likes, {comments:,} comments). "
        f"High interaction-to-view ratio indicates strong hook and audience retention."
    )
    next_ideas = [
        f"Part 2: Deep Dive into {title[:35]}",
        f"Common Mistakes in {title[:35]}",
        f"2026 Checklist: Mastering {title[:30]}",
    ]
    return {
        "post_id": post.post_id,
        "title": title,
        "analysis": analysis,
        "next_ideas": next_ideas,
        "related_posts": related,
        "source": "llm" if llm_analysis else "fallback",
    }


@router.get("/sponsorship-estimate")
def sponsorship_estimate(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return an estimated sponsorship rate range for the current creator."""
    return calculate_sponsorship_rate(db, current_user.user_id)
