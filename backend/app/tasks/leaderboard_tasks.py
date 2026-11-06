"""Celery tasks for daily leaderboard snapshot refresh."""

from __future__ import annotations

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.leaderboard_service import LeaderboardService


@celery_app.task(name="leaderboard.refresh_all")
def refresh_all_leaderboards_task() -> dict:
    db = SessionLocal()
    try:
        service = LeaderboardService(db)
        result = service.refresh_all_snapshots()
        return result
    finally:
        db.close()
