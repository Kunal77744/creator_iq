from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ...models import ContentEmbedding, Creator, Post, PostAnalytics, SocialAccount
from ..llm import generate_ai_text
from .embeddings import embed_text


def _sql_top_posts(db: Session, user_id: int, by_engagement: bool, top_k: int) -> list[dict]:
    """Query PostgreSQL directly for true top posts by views or engagement_rate."""
    order_col = desc(PostAnalytics.engagement_rate) if by_engagement else desc(PostAnalytics.views)
    rows = db.execute(
        select(Post, PostAnalytics, SocialAccount.platform)
        .join(PostAnalytics, PostAnalytics.post_id == Post.post_id)
        .join(SocialAccount, SocialAccount.account_id == Post.account_id)
        .join(Creator, Creator.creator_id == SocialAccount.creator_id)
        .where(Creator.user_id == user_id)
        .order_by(order_col, desc(PostAnalytics.views))
        .limit(top_k)
    ).all()

    return [
        {
            "post_id": post.post_id,
            "title": post.caption or "Untitled",
            "platform": (platform or "Unknown").capitalize(),
            "views": analytics.views or 0,
            "engagement_rate": analytics.engagement_rate or 0.0,
            "chunk_text": f"[{platform}] {post.caption} — {analytics.views} views, {analytics.engagement_rate}% eng",
            "score": 1.0,
        }
        for post, analytics, platform in rows
    ]


def retrieve_similar_chunks(db: Session, user_id: int, query: str, top_k: int = 4) -> list[dict]:
    """Retrieve top-k chunks scoped strictly to user_id (SQL for superlatives, pgvector for semantic search)."""
    q_lower = (query or "").lower()
    if any(w in q_lower for w in ("highest", "top", "best", "most", "max")) and any(
        m in q_lower for m in ("view", "engagement", "perform", "video", "post")
    ):
        has_embeddings = db.scalar(
            select(ContentEmbedding.embedding_id).where(ContentEmbedding.user_id == user_id).limit(1)
        )
        if not has_embeddings:
            return []
        by_eng = "engagement" in q_lower and "view" not in q_lower
        sql_hits = _sql_top_posts(db, user_id, by_engagement=by_eng, top_k=top_k)
        if sql_hits:
            return sql_hits

    query_vec = embed_text(query)
    dist_expr = ContentEmbedding.embedding.cosine_distance(query_vec)

    rows = db.execute(
        select(ContentEmbedding, dist_expr.label("distance"))
        .where(ContentEmbedding.user_id == user_id)
        .order_by(dist_expr.asc())
        .limit(top_k)
    ).all()

    results = []
    for row, distance in rows:
        meta = row.metadata_json or {}
        results.append(
            {
                "post_id": row.post_id,
                "title": meta.get("title", "Untitled"),
                "platform": meta.get("platform", "Unknown"),
                "views": meta.get("views", 0),
                "engagement_rate": meta.get("engagement_rate", 0.0),
                "chunk_type": meta.get("chunk_type", "post"),
                "chunk_text": row.chunk_text,
                "score": round(max(0.0, 1.0 - float(distance)), 4),
            }
        )
    return results


def answer_rag_query(db: Session, user_id: int, query: str) -> dict:
    """Return a grounded answer and source citations from the creator's indexed content."""
    hits = retrieve_similar_chunks(db, user_id, query, top_k=4)
    if not hits:
        return {
            "answer": "No indexed content found for your account yet. Click 'Index Content' after syncing a social channel to enable grounded AI insights.",
            "citations": [],
            "source": "fallback",
        }

    context = "\n".join(
        f"- [{h['platform']} | {h.get('chunk_type', 'post')}] {h['title']} "
        f"({h['views']:,} views, {h['engagement_rate']}% eng): {h['chunk_text']}"
        for h in hits
    )
    llm_answer = generate_ai_text(
        f"User question: {query}\n\nRetrieved creator content & audience comments:\n{context}",
        system_prompt=(
            "You are CreatorIQ AI. Answer concisely using ONLY the retrieved creator metrics "
            "and audience comments above. Cite specific videos or audience feedback when relevant."
        ),
    )
    if llm_answer:
        return {"answer": llm_answer, "citations": hits, "source": "llm"}

    lines = ["Based on your indexed creator content and audience comments in PostgreSQL:"]
    for i, h in enumerate(hits, 1):
        if h.get("chunk_type") == "comments":
            lines.append(f"{i}. [{h['platform']} Comments] {h['title']} — {h['chunk_text'][:220]}")
        else:
            lines.append(
                f"{i}. [{h['platform']}] {h['title']} — {h['views']:,} views, {h['engagement_rate']}% engagement (relevance {h['score']})."
            )
    return {
        "answer": "\n".join(lines),
        "citations": hits,
        "source": "fallback",
    }
