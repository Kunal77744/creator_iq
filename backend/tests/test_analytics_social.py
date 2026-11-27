"""Regression tests for Social Accounts & Analytics endpoints."""


def test_analytics_requires_auth(client):
    """Verify analytics endpoints reject unauthenticated requests with 401."""
    for path in (
        "/api/analytics/overview",
        "/api/analytics/posts",
        "/api/analytics/content-performance",
        "/api/analytics/audience",
        "/api/analytics/marketing/overview",
    ):
        assert client.get(path).status_code == 401, path


def test_youtube_sync_validation_error(client, h):
    """Verify YouTube sync rejects a blank channel handle with 400."""
    r = client.post("/api/analytics/youtube/sync", json={"channel_handle": "   "}, headers=h["creator"])
    assert r.status_code == 400


def test_analytics_overview_and_posts(client, h):
    """Verify creator overview and posts endpoints return valid structures."""
    overview = client.get("/api/analytics/overview", headers=h["creator"])
    assert overview.status_code == 200
    body = overview.json()
    assert "connected" in body and "platforms" in body

    posts_res = client.get("/api/analytics/posts", headers=h["creator"])
    assert posts_res.status_code == 200
    posts_body = posts_res.json()
    assert isinstance(posts_body, list)


def test_content_performance_and_audience(client, h):
    """Verify content performance and audience endpoints return expected metric keys."""
    perf = client.get("/api/analytics/content-performance?days=30", headers=h["creator"])
    assert perf.status_code == 200
    for key in ("Views", "Likes", "Comments", "Shares"):
        assert key in perf.json()

    aud = client.get("/api/analytics/audience?days=30", headers=h["creator"])
    assert aud.status_code == 200
    assert "current_followers" in aud.json()


def test_compare_posts_same_or_missing_fails(client, h):
    """Verify comparing nonexistent post IDs returns 400 or 404."""
    r = client.get("/api/analytics/compare?post_id_1=99999&post_id_2=99998", headers=h["creator"])
    assert r.status_code in (400, 404)


def test_marketing_overview_accessible(client, h):
    """Verify marketing team users can access the marketing overview endpoint."""
    r = client.get("/api/analytics/marketing/overview", headers=h["marketing"])
    assert r.status_code == 200
    assert "kpis" in r.json()


def test_new_creator_starts_with_no_fake_channel(client):
    """Verify a newly registered creator has no pre-connected social channel."""
    from .conftest import auth, register

    register(client, email="fresh_user@example.com", role="creator", name="Fresh Creator")
    headers = auth(client, "fresh_user@example.com", "Pass1234")
    r = client.get("/api/v1/analytics/overview", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["connected"] is False
    assert body["channel_name"] is None


def test_two_creators_can_sync_same_public_channel(client, h, monkeypatch):
    """Verify two different creators can independently sync the same public YouTube handle."""
    from .conftest import auth, register

    # Force demo fallback in test so no external YouTube quota/network is needed
    monkeypatch.setattr("app.services.youtube.YOUTUBE_API_KEY", "")

    r1 = client.post("/api/v1/analytics/youtube/sync", json={"channel_handle": "@chaiaurcode"}, headers=h["creator"])
    assert r1.status_code == 200, r1.text

    register(client, email="kunal2@example.com", role="creator", name="Kunal 2")
    h2 = auth(client, "kunal2@example.com", "Pass1234")
    r2 = client.post("/api/v1/analytics/youtube/sync", json={"channel_handle": "@chaiaurcode"}, headers=h2)
    assert r2.status_code == 200, r2.text
