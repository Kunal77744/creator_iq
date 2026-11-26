from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Notification, User

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


def _seed_if_empty(user: User, db: Session) -> None:
    exists = db.scalar(select(Notification.notification_id).where(Notification.user_id == user.user_id))
    if exists:
        return
    samples = [
        ("Engagement Spike Detected", "Your latest YouTube video crossed 7.5% engagement rate, 18% above your 30-day average.", "engagement"),
        ("Sponsorship Payout Received", "Notion AI Campus Campaign (₹24,000) has been marked as paid.", "revenue"),
        ("Weekly Analytics Report Ready", "Your weekly multi-platform performance summary is ready to export in Reports.", "performance"),
        ("Peak Audience Window", "Most of your audience is active between 18:00 - 21:00 IST. Schedule your next upload accordingly.", "performance"),
    ]
    for title, msg, cat in samples:
        db.add(Notification(user_id=user.user_id, title=title, message=msg, category=cat, is_read=False))
    db.commit()


@router.get("")
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _seed_if_empty(current_user, db)
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.user_id)
        .order_by(Notification.notification_id.desc())
    ).all()
    unread = sum(1 for r in rows if not r.is_read)
    return {
        "unread_count": unread,
        "items": [
            {
                "notification_id": r.notification_id,
                "title": r.title,
                "message": r.message,
                "category": r.category,
                "is_read": r.is_read,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.patch("/{notification_id}/read")
def mark_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.scalar(
        select(Notification).where(
            Notification.notification_id == notification_id, Notification.user_id == current_user.user_id
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    row.is_read = True
    db.commit()
    return {"status": "ok"}


@router.post("/read-all")
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        update(Notification).where(Notification.user_id == current_user.user_id).values(is_read=True)
    )
    db.commit()
    return {"status": "ok"}
