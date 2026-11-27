"""TDD RED Phase: Tests for RAG SQL superlative ranking, source transparency, and AI input limits."""
from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Creator, Post, PostAnalytics, SocialAccount, User


def test_ai_endpoints_reject_oversized_inputs(client, h):
    too_long = "x" * 1005
    r1 = client.post("/api/v1/ai/rag-query", json={"query": too_long}, headers=h["creator"])
    assert r1.status_code == 422

    r2 = client.post("/api/v1/ai/agent-chat", json={"message": too_long}, headers=h["creator"])
    assert r2.status_code == 422


def test_ai_responses_include_transparent_source_field(client, h):
    ins = client.get("/api/v1/ai/insights", headers=h["creator"])
    assert ins.status_code == 200
    assert ins.json()["source"] in ("llm", "fallback")

    ag = client.post("/api/v1/ai/agent-chat", json={"message": "Give me my KPIs"}, headers=h["creator"])
    assert ag.status_code == 200
    assert ag.json()["source"] in ("llm", "llm_function_calling", "rule_based_fallback")


def test_rag_superlative_finds_true_top_video_beyond_20_posts(client, h):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "creator@creatoriq.com"))
        creator = db.scalar(select(Creator).where(Creator.user_id == user.user_id))
        if not creator:
            creator = Creator(user_id=user.user_id, creator_name=user.name)
            db.add(creator)
            db.commit()
            db.refresh(creator)

        acc = SocialAccount(
            creator_id=creator.creator_id,
            platform="youtube",
            username="@scale_creator",
            platform_user_id="yt_scale_1",
            followers=50000,
            total_views=2000000,
            video_count=25,
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)

        # Insert 25 posts; post #25 has completely unrelated title but 9,999,999 views
        for i in range(25):
            views = 9_999_999 if i == 24 else 1000 + i
            title = "Zebra Quantum Origami" if i == 24 else f"Video views engagement topic {i}"
            p = Post(
                account_id=acc.account_id,
                platform_post_id=f"v_{i}",
                content_type="video",
                caption=title,
                published_at=datetime.utcnow(),
            )
            db.add(p)
            db.commit()
            db.refresh(p)
            db.add(PostAnalytics(post_id=p.post_id, views=views, likes=100, comments=10, engagement_rate=5.0))
        db.commit()

    client.post("/api/v1/ai/index", headers=h["creator"])
    r = client.post(
        "/api/v1/ai/rag-query",
        json={"query": "Which video has the highest views?"},
        headers=h["creator"],
    )
    assert r.status_code == 200
    cites = r.json()["citations"]
    assert len(cites) > 0
    assert cites[0]["views"] == 9_999_999
