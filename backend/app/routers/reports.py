"""CSV report export endpoints for analytics, revenue, and connected platform summaries."""

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Creator, Post, RevenueEntry, SocialAccount, User

router = APIRouter(prefix="/reports", tags=["Reports & Export"])


@router.get("/export")
def export_report(
    report_type: str = Query("analytics", pattern="^(analytics|revenue|platforms)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export analytics, revenue, or platform comparison as a CSV (Excel-compatible) file."""
    # Write CSV rows into an in-memory buffer based on the requested report type
    buf = io.StringIO()
    writer = csv.writer(buf)

    if report_type == "revenue":
        # Export all revenue entries for the current user
        writer.writerow(["ID", "Title", "Source", "Platform", "Amount (INR)", "Status", "Earned Date"])
        rows = db.scalars(
            select(RevenueEntry)
            .where(RevenueEntry.user_id == current_user.user_id)
            .order_by(RevenueEntry.earned_at.desc())
        ).all()
        for r in rows:
            writer.writerow([r.revenue_id, r.title, r.source, r.platform, r.amount, r.status, r.earned_at.isoformat()])
        filename = "creatoriq_revenue_report.csv"

    elif report_type == "platforms":
        # Export summary stats for each connected social account
        writer.writerow(["Platform", "Username", "Followers", "Total Views", "Videos/Posts", "Live Sync"])
        creator = db.scalar(select(Creator).where(Creator.user_id == current_user.user_id))
        accounts = (
            db.scalars(select(SocialAccount).where(SocialAccount.creator_id == creator.creator_id)).all()
            if creator else []
        )
        for a in accounts:
            writer.writerow([a.platform.capitalize(), a.username or a.platform_user_id, a.followers, a.total_views, a.video_count, a.is_live])
        filename = "creatoriq_platforms_report.csv"

    else:
        # Export post-level analytics across all connected accounts
        writer.writerow(["Post ID", "Title", "Platform", "Type", "Views", "Likes", "Comments", "Shares", "Engagement %", "Published At"])
        creator = db.scalar(select(Creator).where(Creator.user_id == current_user.user_id))
        if creator:
            accounts = db.scalars(select(SocialAccount).where(SocialAccount.creator_id == creator.creator_id)).all()
            acc_map = {a.account_id: a.platform for a in accounts}
            posts = db.scalars(select(Post).where(Post.account_id.in_(list(acc_map.keys())))).all() if acc_map else []
            for p in posts:
                a = p.analytics
                writer.writerow([
                    p.post_id,
                    (p.caption or "Untitled").replace("\n", " "),
                    acc_map.get(p.account_id, "").capitalize(),
                    p.content_type or "video",
                    a.views if a else 0,
                    a.likes if a else 0,
                    a.comments if a else 0,
                    a.shares if a else 0,
                    a.engagement_rate if a else 0.0,
                    p.published_at.isoformat() if p.published_at else "",
                ])
        filename = "creatoriq_analytics_report.csv"

    # Stream the generated CSV back with a download attachment header
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
