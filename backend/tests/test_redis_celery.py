"""TDD RED Phase: Tests for Redis caching, Celery worker tasks, and /api/v1/ routes."""


def test_v1_health_reports_db_and_redis(client):
    """Verify /api/v1/health reports healthy status for both database and Redis."""
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["redis"] == "ok"


def test_v1_routes_require_auth_and_work(client, h):
    """Verify /api/v1 analytics and revenue routes enforce auth and return data."""
    assert client.get("/api/v1/analytics/overview").status_code == 401
    r = client.get("/api/v1/analytics/overview", headers=h["creator"])
    assert r.status_code == 200
    assert "subscribers" in r.json()

    rev = client.get("/api/v1/revenue", headers=h["creator"])
    assert rev.status_code == 200


def test_redis_cache_roundtrip():
    """Verify Redis cache_set, cache_get, and cache_delete roundtrip behavior."""
    from app.core.redis import cache_delete, cache_get, cache_set

    key = "test:creatoriq:phase2"
    cache_delete(key)
    assert cache_get(key) is None

    cache_set(key, {"views": 1234, "ok": True}, ttl_seconds=30)
    cached = cache_get(key)
    assert cached == {"views": 1234, "ok": True}

    cache_delete(key)
    assert cache_get(key) is None


def test_analytics_overview_populates_redis_cache(client, h):
    """Verify analytics overview caches its response in Redis for subsequent requests."""
    from app.core.redis import cache_delete, cache_get

    # Clear any prior cache for creator
    me = client.get("/api/v1/auth/me", headers=h["creator"]).json()
    cache_key = f"analytics:overview:{me['user_id']}:all:30"
    cache_delete(cache_key)

    r1 = client.get("/api/v1/analytics/overview?days=30", headers=h["creator"])
    assert r1.status_code == 200
    assert cache_get(cache_key) is not None

    # Second call should return identical cached payload
    r2 = client.get("/api/v1/analytics/overview?days=30", headers=h["creator"])
    assert r2.status_code == 200
    assert r2.json() == r1.json()


def test_celery_app_and_sync_task_registered():
    """Verify the YouTube sync Celery task is registered and runs cleanly in eager mode."""
    from app.workers.celery_app import celery_app
    from app.workers.tasks import sync_all_youtube_channels_task

    assert celery_app is not None
    assert sync_all_youtube_channels_task.name in celery_app.tasks
    # Eager execution should succeed cleanly even with 0 live channels
    celery_app.conf.task_always_eager = True
    result = sync_all_youtube_channels_task.delay()
    assert isinstance(result.get(), dict)
    assert "synced" in result.get()
