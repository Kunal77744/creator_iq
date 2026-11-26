"""TDD RED/GREEN: Tests for RAG pipeline (pgvector indexing, multi-tenant retrieval, endpoints)."""
from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Creator, Post, PostAnalytics, SocialAccount, User
from .conftest import auth, register


def _seed_creator_posts(email: str = "creator@creatoriq.com") -> None:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        creator = db.scalar(select(Creator).where(Creator.user_id == user.user_id))
        if not creator:
            creator = Creator(user_id=user.user_id, creator_name=user.name)
            db.add(creator)
            db.commit()
            db.refresh(creator)

        acc = db.scalar(select(SocialAccount).where(SocialAccount.creator_id == creator.creator_id))
        if not acc:
            acc = SocialAccount(
                creator_id=creator.creator_id,
                platform="youtube",
                username="@testcreator",
                platform_user_id=f"yt_{user.user_id}",
                followers=120000,
                total_views=1500000,
                video_count=2,
                is_live=False,
            )
            db.add(acc)
            db.commit()
            db.refresh(acc)

        p1 = Post(
            account_id=acc.account_id,
            platform_post_id=f"vid_1_{user.user_id}",
            content_type="video",
            caption="FastAPI + pgvector RAG Tutorial for Beginners",
            hashtags="#python #fastapi #ai",
            published_at=datetime.utcnow(),
        )
        p2 = Post(
            account_id=acc.account_id,
            platform_post_id=f"vid_2_{user.user_id}",
            content_type="video",
            caption="How I Built a Multi-Agent SaaS Dashboard",
            hashtags="#react #agents #saas",
            published_at=datetime.utcnow(),
        )
        db.add_all([p1, p2])
        db.commit()
        db.refresh(p1)
        db.refresh(p2)

        db.add_all([
            PostAnalytics(post_id=p1.post_id, views=95000, likes=7200, comments=480, shares=310, engagement_rate=8.4),
            PostAnalytics(post_id=p2.post_id, views=64000, likes=4100, comments=220, shares=150, engagement_rate=6.9),
        ])
        db.commit()


def test_ai_rag_endpoints_require_auth(client):
    assert client.post("/api/v1/ai/index").status_code == 401
    assert client.post("/api/v1/ai/rag-query", json={"query": "top videos"}).status_code == 401


def test_rag_query_empty_state_returns_clean_message(client, h):
    r = client.post("/api/v1/ai/rag-query", json={"query": "best performing video"}, headers=h["creator"])
    assert r.status_code == 200
    body = r.json()
    assert body["citations"] == []
    assert "answer" in body and len(body["answer"]) > 0


def test_rag_index_and_retrieve_with_citations(client, h):
    _seed_creator_posts()

    idx = client.post("/api/v1/ai/index", headers=h["creator"])
    assert idx.status_code == 200
    assert idx.json()["indexed_chunks"] > 0

    rag = client.post(
        "/api/v1/ai/rag-query",
        json={"query": "which videos had high views and engagement with FastAPI"},
        headers=h["creator"],
    )
    assert rag.status_code == 200
    body = rag.json()
    assert len(body["citations"]) > 0
    assert "FastAPI" in body["citations"][0]["title"] or "views" in body["answer"]


def test_rag_multi_tenant_isolation(client, h):
    _seed_creator_posts()
    idx = client.post("/api/v1/ai/index", headers=h["creator"])
    assert idx.json()["indexed_chunks"] > 0

    # Creator 2 registers fresh (no content indexed)
    register(client, email="isolated_creator@example.com", role="creator")
    other_h = auth(client, "isolated_creator@example.com", "Pass1234")

    rag = client.post(
        "/api/v1/ai/rag-query",
        json={"query": "FastAPI views engagement"},
        headers=other_h,
    )
    assert rag.status_code == 200
    # Must NOT leak Creator 1's embeddings
    assert rag.json()["citations"] == []
