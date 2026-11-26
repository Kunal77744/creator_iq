"""Regression tests for Social Accounts & Analytics endpoints."""


def test_analytics_requires_auth(client):
    for path in (
        "/api/analytics/overview",
        "/api/analytics/posts",
        "/api/analytics/content-performance",
        "/api/analytics/audience",
        "/api/analytics/marketing/overview",
    ):
        assert client.get(path).status_code == 401, path


def test_youtube_sync_validation_error(client, h):
    r = client.post("/api/analytics/youtube/sync", json={"channel_handle": "   "}, headers=h["creator"])
    assert r.status_code == 400


def test_analytics_overview_and_posts(client, h):
    overview = client.get("/api/analytics/overview", headers=h["creator"])
    assert overview.status_code == 200
    body = overview.json()
    assert "connected" in body and "platforms" in body

    posts_res = client.get("/api/analytics/posts", headers=h["creator"])
    assert posts_res.status_code == 200
    posts_body = posts_res.json()
    assert isinstance(posts_body, list)


def test_content_performance_and_audience(client, h):
    perf = client.get("/api/analytics/content-performance?days=30", headers=h["creator"])
    assert perf.status_code == 200
    for key in ("Views", "Likes", "Comments", "Shares"):
        assert key in perf.json()

    aud = client.get("/api/analytics/audience?days=30", headers=h["creator"])
    assert aud.status_code == 200
    assert "current_followers" in aud.json()


def test_compare_posts_same_or_missing_fails(client, h):
    r = client.get("/api/analytics/compare?post_id_1=99999&post_id_2=99998", headers=h["creator"])
    assert r.status_code in (400, 404)


def test_marketing_overview_accessible(client, h):
    r = client.get("/api/analytics/marketing/overview", headers=h["marketing"])
    assert r.status_code == 200
    assert "kpis" in r.json()
