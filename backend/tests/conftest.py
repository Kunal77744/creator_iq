"""Pytest configuration, isolated PostgreSQL/Redis fixtures, and auth helper functions."""

import os

# Must be set before the app is imported.
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5433/creatoriq_test",
)
os.environ["SECRET_KEY"] = "test-secret-key-for-creatoriq-ci-only-32b"
os.environ["SEED_DEMO_USERS"] = "false"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["DISABLE_RATE_LIMIT"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import DEMO_PASSWORD, seed_demo_users  # noqa: E402


@pytest.fixture()
def client():
    """Fresh PostgreSQL + pgvector schema and clean Redis cache before every test."""
    from app.core.redis import cache_delete_prefix

    cache_delete_prefix("analytics:")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo_users(db)
    with TestClient(app) as c:
        yield c


def login(client, email, password=DEMO_PASSWORD):
    """Post OAuth2 login form credentials and return the raw response."""
    return client.post("/api/auth/login", data={"username": email, "password": password})


def auth(client, email, password=DEMO_PASSWORD):
    """Log in a user and return a Bearer Authorization header dict."""
    r = login(client, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def register(client, **over):
    """Register a new test user with default values merged with any overrides."""
    body = {"name": "Test User", "email": "new@example.com", "password": "Pass1234", "role": "creator"}
    body.update(over)
    return client.post("/api/auth/register", json=body)


@pytest.fixture()
def h(client):
    """Auth headers for each demo role."""
    return {
        "creator": auth(client, "creator@creatoriq.com"),
        "agency": auth(client, "agency@creatoriq.com"),
        "marketing": auth(client, "marketing@creatoriq.com"),
        "admin": auth(client, "admin@creatoriq.com"),
    }
