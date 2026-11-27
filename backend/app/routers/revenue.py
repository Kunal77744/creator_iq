"""Revenue and monetization endpoints for listing, creating, and deleting income entries."""

from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import RevenueEntry, User

router = APIRouter(prefix="/revenue", tags=["Revenue & Monetization"])

SOURCE_LABELS = {
    "sponsorship": "Sponsorships",
    "ad_revenue": "Ad Revenue",
    "affiliate": "Affiliate Marketing",
    "brand_collab": "Brand Collaborations",
    "subscription": "Subscriptions",
}


class RevenueCreate(BaseModel):
    """Validation schema for creating a new revenue entry."""

    source: Literal["sponsorship", "ad_revenue", "affiliate", "brand_collab", "subscription"] = "sponsorship"
    title: str = Field(min_length=2, max_length=150)
    platform: str = Field(default="YouTube", max_length=50)
    amount: float = Field(gt=0)
    status: Literal["paid", "pending"] = "paid"
    earned_at: Optional[date] = None


def _seed_if_empty(user: User, db: Session) -> None:
    """Seed sample revenue entries once for @creatoriq.com demo accounts if none exist."""
    if not user.email.endswith("@creatoriq.com"):
        return
    exists = db.scalar(select(RevenueEntry.revenue_id).where(RevenueEntry.user_id == user.user_id))
    if exists:
        return
    today = date.today()
    samples = [
        ("sponsorship", "Notion AI Campus Campaign", "YouTube", 24000.0, "paid", today - timedelta(days=3)),
        ("ad_revenue", "YouTube AdSense Monthly Payout", "YouTube", 14500.0, "paid", today - timedelta(days=8)),
        ("brand_collab", "Boat Audio Reel Integration", "Instagram", 18000.0, "paid", today - timedelta(days=14)),
        ("affiliate", "Amazon Tech Gear Links", "YouTube", 6200.0, "paid", today - timedelta(days=19)),
        ("subscription", "Channel Memberships", "YouTube", 4800.0, "paid", today - timedelta(days=25)),
        ("sponsorship", "Scaler Dev Workshop Promo", "LinkedIn", 15000.0, "pending", today - timedelta(days=1)),
    ]
    for src, title, plat, amt, st, dt in samples:
        db.add(RevenueEntry(
            user_id=user.user_id, source=src, title=title, platform=plat, amount=amt, status=st, earned_at=dt
        ))
    db.commit()


@router.get("")
def list_revenue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all revenue entries for the current user with totals and source breakdown."""
    # Seed demo entries if applicable and query all entries newest-first
    _seed_if_empty(current_user, db)
    rows = db.scalars(
        select(RevenueEntry)
        .where(RevenueEntry.user_id == current_user.user_id)
        .order_by(RevenueEntry.earned_at.desc(), RevenueEntry.revenue_id.desc())
    ).all()

    # Compute total, paid, and pending amounts plus breakdown by revenue source
    total = sum(r.amount for r in rows)
    paid = sum(r.amount for r in rows if r.status == "paid")
    pending = sum(r.amount for r in rows if r.status != "paid")

    by_source: dict[str, float] = {}
    for r in rows:
        label = SOURCE_LABELS.get(r.source, r.source.title())
        by_source[label] = by_source.get(label, 0.0) + r.amount

    return {
        "summary": {
            "total": round(total, 2),
            "paid": round(paid, 2),
            "pending": round(pending, 2),
            "count": len(rows),
        },
        "breakdown": [{"name": k, "value": round(v, 2)} for k, v in by_source.items()],
        "entries": [
            {
                "revenue_id": r.revenue_id,
                "source": r.source,
                "source_label": SOURCE_LABELS.get(r.source, r.source),
                "title": r.title,
                "platform": r.platform,
                "amount": r.amount,
                "status": r.status,
                "earned_at": r.earned_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_revenue(data: RevenueCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new revenue entry for the authenticated user."""
    entry = RevenueEntry(
        user_id=current_user.user_id,
        source=data.source,
        title=data.title.strip(),
        platform=data.platform.strip() or "YouTube",
        amount=data.amount,
        status=data.status,
        earned_at=data.earned_at or date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "revenue_id": entry.revenue_id,
        "source": entry.source,
        "source_label": SOURCE_LABELS.get(entry.source, entry.source),
        "title": entry.title,
        "platform": entry.platform,
        "amount": entry.amount,
        "status": entry.status,
        "earned_at": entry.earned_at.isoformat(),
    }


@router.delete("/{revenue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue(revenue_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a revenue entry owned by the authenticated user."""
    row = db.scalar(
        select(RevenueEntry).where(
            RevenueEntry.revenue_id == revenue_id, RevenueEntry.user_id == current_user.user_id
        )
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Revenue entry not found")
    db.delete(row)
    db.commit()
