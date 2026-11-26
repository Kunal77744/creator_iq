import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from .config import FRONTEND_ORIGIN, SEED_DEMO_USERS, SYNC_INTERVAL_MINUTES, YOUTUBE_API_KEY
from .core.redis import redis_ping
from .database import SessionLocal
from .routers import account, admin, agencies, ai, analytics, auth, creators, notifications, reports, revenue
from .seed import seed_demo_users
from .models import SocialAccount
from .services.youtube import sync_youtube_channel_to_db

log = logging.getLogger("creatoriq")


def _resync_all() -> None:
    """Re-sync every live YouTube account -> stores today's follower snapshot (real growth history)."""
    with SessionLocal() as db:
        accounts = db.scalars(select(SocialAccount).where(
            SocialAccount.platform == "youtube", SocialAccount.is_live.is_(True))).all()
        for acc in accounts:
            try:
                sync_youtube_channel_to_db(db, acc.creator_id, acc.username or acc.platform_user_id)
            except Exception as e:  # keep the loop alive
                db.rollback()
                log.warning("Auto-sync failed for %s: %s", acc.username, e)


async def _sync_loop() -> None:
    while True:
        await asyncio.sleep(SYNC_INTERVAL_MINUTES * 60)
        await asyncio.to_thread(_resync_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed strictly by Alembic migrations (`alembic upgrade head`).
    if SEED_DEMO_USERS:
        try:
            with SessionLocal() as db:
                seed_demo_users(db)
        except (OperationalError, ProgrammingError):
            log.error("Database tables not found. Run: alembic upgrade head")
    task = None
    if YOUTUBE_API_KEY and SYNC_INTERVAL_MINUTES > 0:
        task = asyncio.create_task(_sync_loop())
    yield
    if task:
        task.cancel()


app = FastAPI(title="CreatorIQ API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

v1_router = APIRouter(prefix="/api/v1")
legacy_router = APIRouter(prefix="/api", include_in_schema=False)

for r in (auth, account, creators, agencies, admin, analytics, revenue, notifications, reports, ai):
    v1_router.include_router(r.router)
    legacy_router.include_router(r.router)

app.include_router(v1_router)
app.include_router(legacy_router)


@app.get("/api/v1/health", tags=["Health"])
@app.get("/api/health", tags=["Health"], include_in_schema=False)
def health():
    db_ok = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False
    redis_ok = redis_ping()
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
