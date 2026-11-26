import logging

from sqlalchemy import select

from ..core.redis import cache_delete_prefix
from ..database import SessionLocal
from ..models import SocialAccount
from ..services.youtube import sync_youtube_channel_to_db
from .celery_app import celery_app

log = logging.getLogger("creatoriq.workers")


@celery_app.task(name="app.workers.tasks.sync_all_youtube_channels_task")
def sync_all_youtube_channels_task() -> dict:
    """Re-sync all live YouTube accounts in PostgreSQL and invalidate cached analytics."""
    synced = 0
    errors: list[str] = []
    with SessionLocal() as db:
        accounts = db.scalars(
            select(SocialAccount).where(
                SocialAccount.platform == "youtube",
                SocialAccount.is_live.is_(True),
            )
        ).all()
        for acc in accounts:
            try:
                sync_youtube_channel_to_db(db, acc.creator_id, acc.username or acc.platform_user_id)
                synced += 1
            except Exception as exc:
                db.rollback()
                log.warning("Celery YouTube sync failed for %s: %s", acc.username, exc)
                errors.append(str(exc))
    if synced:
        cache_delete_prefix("analytics:overview:")
    return {"synced": synced, "errors": errors}
