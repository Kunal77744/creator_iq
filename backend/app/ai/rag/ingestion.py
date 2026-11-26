from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...models import ContentEmbedding, Creator, Post, SocialAccount
from .chunker import chunk_text
from .embeddings import embed_text


def index_creator_content(db: Session, user_id: int) -> int:
    """Ingest all posts + analytics for a creator into pgvector content_embeddings."""
    creator = db.scalar(select(Creator).where(Creator.user_id == user_id))
    if not creator:
        return 0

    accounts = db.scalars(
        select(SocialAccount).where(SocialAccount.creator_id == creator.creator_id)
    ).all()
    if not accounts:
        return 0

    acc_map = {a.account_id: a for a in accounts}
    posts = db.scalars(
        select(Post).where(Post.account_id.in_(list(acc_map.keys())))
    ).all()

    # Replace existing embeddings for this user to keep index fresh
    db.execute(delete(ContentEmbedding).where(ContentEmbedding.user_id == user_id))

    total_chunks = 0
    for post in posts:
        acc = acc_map.get(post.account_id)
        platform = acc.platform.capitalize() if acc else "Unknown"
        a = post.analytics
        doc = (
            f"Platform: {platform}. "
            f"Title: {post.caption or 'Untitled'}. "
            f"Type: {post.content_type or 'video'}. "
            f"Hashtags: {post.hashtags or 'none'}. "
            f"Views: {a.views if a else 0}, Likes: {a.likes if a else 0}, "
            f"Comments: {a.comments if a else 0}, Shares: {a.shares if a else 0}, "
            f"Engagement Rate: {a.engagement_rate if a else 0.0}%."
        )
        for chunk in chunk_text(doc):
            db.add(
                ContentEmbedding(
                    user_id=user_id,
                    post_id=post.post_id,
                    chunk_text=chunk,
                    metadata_json={
                        "post_id": post.post_id,
                        "title": post.caption or "Untitled",
                        "platform": platform,
                        "views": a.views if a else 0,
                        "engagement_rate": a.engagement_rate if a else 0.0,
                    },
                    embedding=embed_text(chunk),
                )
            )
            total_chunks += 1

    db.commit()
    return total_chunks
