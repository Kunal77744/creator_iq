"""TDD RED Phase: Tests for embedded AI features (Growth Brief, Post Deep-Dive, Sponsorship Estimator, LLM client)."""
from .conftest import auth, register
from .test_ai_rag import _seed_creator_posts


def test_embedded_ai_endpoints_require_auth(client):
    assert client.get("/api/v1/ai/insights").status_code == 401
    assert client.post("/api/v1/ai/analyze-post/1").status_code == 401
    assert client.get("/api/v1/ai/sponsorship-estimate").status_code == 401


def test_ai_insights_empty_state_and_populated(client, h):
    # Empty state when creator has no posts
    empty = client.get("/api/v1/ai/insights", headers=h["creator"])
    assert empty.status_code == 200
    assert empty.json()["has_data"] is False
    assert len(empty.json()["insights"]) >= 1

    # Populated state
    _seed_creator_posts()
    res = client.get("/api/v1/ai/insights", headers=h["creator"])
    assert res.status_code == 200
    body = res.json()
    assert body["has_data"] is True
    assert isinstance(body["insights"], list) and len(body["insights"]) >= 2
    assert "summary" in body


def test_analyze_post_rag_and_isolation(client, h):
    _seed_creator_posts()
    posts = client.get("/api/v1/analytics/posts", headers=h["creator"]).json()
    post_id = posts[0]["post_id"]

    res = client.post(f"/api/v1/ai/analyze-post/{post_id}", headers=h["creator"])
    assert res.status_code == 200
    body = res.json()
    assert body["post_id"] == post_id
    assert "analysis" in body and len(body["analysis"]) > 0
    assert isinstance(body["next_ideas"], list) and len(body["next_ideas"]) >= 2

    # Another user must not access creator's post analysis
    register(client, email="other_ai@example.com", role="creator")
    other_h = auth(client, "other_ai@example.com", "Pass1234")
    forbidden = client.post(f"/api/v1/ai/analyze-post/{post_id}", headers=other_h)
    assert forbidden.status_code == 404


def test_sponsorship_estimate_returns_inr_range(client, h):
    _seed_creator_posts()
    res = client.get("/api/v1/ai/sponsorship-estimate", headers=h["creator"])
    assert res.status_code == 200
    body = res.json()
    assert body["recommended_rate_inr"] > 0
    assert body["range_min_inr"] <= body["recommended_rate_inr"] <= body["range_max_inr"]


def test_llm_client_graceful_fallback_without_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    from app.ai.llm import llm_is_configured

    assert llm_is_configured() is False
