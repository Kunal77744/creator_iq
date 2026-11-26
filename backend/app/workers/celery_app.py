from celery import Celery

from ..config import REDIS_URL

celery_app = Celery(
    "creatoriq",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-youtube-channels-every-6h": {
            "task": "app.workers.tasks.sync_all_youtube_channels_task",
            "schedule": 6 * 60 * 60,
        }
    },
)
