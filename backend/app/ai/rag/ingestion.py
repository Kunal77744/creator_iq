from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...models import ContentEmbedding, Creator, Post, SocialAccount
from ...services.youtube import fetch_video_comments
from .chunker import chunk_text
from .embeddings import embed_text


def index_creator_content(db: Session, user_id: int) -> int:
    """Ingest all posts + analytics + top YouTube audience comments into pgvector."""
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

    # Pick top 5 YouTube videos by views for comment ingestion (low quota: max 5 units)
    yt_posts = [
        p for p in posts
        if acc_map.get(p.account_id) and acc_map[p.account_id].platform.lower() == "youtube"
    ]
    yt_posts.sort(key=lambda p: p.analytics.views if p.analytics else 0, reverse=True)
    comment_target_ids = {p.post_id for p in yt_posts[:5]}

    total_chunks = 0
    for post in posts:
        acc = acc_map.get(post.account_id)
        platform = acc.platform.capitalize() if acc else "Unknown"
        a = post.analytics
        views = a.views if a else 0
        eng = a.engagement_rate if a else 0.0
        doc = (
            f"Platform: {platform}. "
            f"Title: {post.caption or 'Untitled'}. "
            f"Type: {post.content_type or 'video'}. "
            f"Hashtags: {post.hashtags or 'none'}. "
            f"Views: {views}, Likes: {a.likes if a else 0}, "
            f"Comments: {a.comments if a else 0}, Shares: {a.shares if a else 0}, "
            f"Engagement Rate: {eng}%."
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
                        "views": views,
                        "engagement_rate": eng,
                        "chunk_type": "post",
                    },
                    embedding=embed_text(chunk),
                )
            )
            total_chunks += 1

        if post.post_id in comment_target_ids and acc is not None:
            comments = fetch_video_comments(
                post.platform_post_id,
                max_results=12,
                is_live=bool(acc.is_live),
            )
            if comments:
                comment_doc = (
                    f"Audience Comments on YouTube video '{post.caption or 'Untitled'}': "
                    + " | ".join(comments)
                )
                for chunk in chunk_text(comment_doc):
                    db.add(
                        ContentEmbedding(
                            user_id=user_id,
                            post_id=post.post_id,
                            chunk_text=chunk,
                            metadata_json={
                                "post_id": post.post_id,
                                "title": post.caption or "Untitled",
                                "platform": platform,
                                "views": views,
                                "engagement_rate": eng,
                                "chunk_type": "comments",
                            },
                            embedding=embed_text(chunk),
                        )
                    )
                    total_chunks += 1

    db.commit()
    return total_chunks
