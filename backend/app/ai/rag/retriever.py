from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import ContentEmbedding
from ..llm import generate_ai_text
from .embeddings import embed_text


def retrieve_similar_chunks(db: Session, user_id: int, query: str, top_k: int = 4) -> list[dict]:
    """Retrieve top-k chunks scoped strictly to user_id via pgvector cosine distance + metric reranking."""
    query_vec = embed_text(query)
    dist_expr = ContentEmbedding.embedding.cosine_distance(query_vec)

    fetch_limit = max(top_k * 5, 20)
    rows = db.execute(
        select(ContentEmbedding, dist_expr.label("distance"))
        .where(ContentEmbedding.user_id == user_id)
        .order_by(dist_expr.asc())
        .limit(fetch_limit)
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
                "chunk_text": row.chunk_text,
                "score": round(max(0.0, 1.0 - float(distance)), 4),
            }
        )

    q_lower = (query or "").lower()
    if any(w in q_lower for w in ("highest", "top", "best", "most", "max")):
        if "engagement" in q_lower and "view" not in q_lower:
            results.sort(key=lambda r: (r["engagement_rate"], r["views"]), reverse=True)
        else:
            results.sort(key=lambda r: (r["views"], r["engagement_rate"]), reverse=True)

    return results[:top_k]


def answer_rag_query(db: Session, user_id: int, query: str) -> dict:
    """Return a grounded answer and source citations from the creator's indexed content."""
    hits = retrieve_similar_chunks(db, user_id, query, top_k=4)
    if not hits:
        return {
            "answer": "No indexed content found for your account yet. Click 'Index Content' after syncing a social channel to enable grounded AI insights.",
            "citations": [],
        }

    context = "\n".join(
        f"- [{h['platform']}] {h['title']} ({h['views']:,} views, {h['engagement_rate']}% eng)"
        for h in hits
    )
    llm_answer = generate_ai_text(
        f"User question: {query}\n\nRetrieved creator content:\n{context}",
        system_prompt="You are CreatorIQ AI. Answer concisely using ONLY the retrieved creator metrics above.",
    )
    if llm_answer:
        return {"answer": llm_answer, "citations": hits}

    lines = ["Based on your indexed creator content in PostgreSQL:"]
    for i, h in enumerate(hits, 1):
        lines.append(
            f"{i}. [{h['platform']}] {h['title']} — {h['views']:,} views, {h['engagement_rate']}% engagement (relevance {h['score']})."
        )
    return {
        "answer": "\n".join(lines),
        "citations": hits,
    }
