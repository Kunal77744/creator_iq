"""TDD RED Phase: Security & validation hardening tests."""
from app.main import app


def test_instagram_sync_fails_cleanly_without_hardcoded_key(client, h, monkeypatch):
    monkeypatch.setattr("app.services.instagram.RAPIDAPI_KEY", "")
    r = client.post("/api/v1/analytics/instagram/sync", json={"username": "testuser"}, headers=h["creator"])
    assert r.status_code == 503


def test_cors_does_not_allow_wildcard_with_credentials():
    cors_mw = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"]
    assert len(cors_mw) == 1
    origins = cors_mw[0].kwargs.get("allow_origins", [])
    assert "*" not in origins


def test_revenue_rejects_invalid_source_or_status_with_422(client, h):
    r1 = client.post(
        "/api/v1/revenue",
        json={"source": "crypto_scam", "title": "Bad Source", "amount": 500},
        headers=h["creator"],
    )
    assert r1.status_code == 422

    r2 = client.post(
        "/api/v1/revenue",
        json={"source": "sponsorship", "title": "Bad Status", "amount": 500, "status": "cancelled"},
        headers=h["creator"],
    )
    assert r2.status_code == 422


def test_linkedin_callback_invalid_state_returns_401_not_500(client):
    r = client.get("/api/v1/auth/linkedin/callback?code=abc&state=not-a-jwt", follow_redirects=False)
    assert r.status_code == 401


def test_rate_limit_blocks_excess_requests_with_429(monkeypatch):
    import pytest
    from fastapi import HTTPException
    from app.core import rate_limit as rl

    monkeypatch.setenv("DISABLE_RATE_LIMIT", "0")
    monkeypatch.setattr(rl, "get_redis_client", lambda: None)
    rl.reset_rate_limits()

    for _ in range(3):
        rl.check_rate_limit("test:127.0.0.1", limit=3, window_seconds=60)

    with pytest.raises(HTTPException) as exc:
        rl.check_rate_limit("test:127.0.0.1", limit=3, window_seconds=60)
    assert exc.value.status_code == 429
    rl.reset_rate_limits()
