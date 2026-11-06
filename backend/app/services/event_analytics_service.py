"""Aggregate client event logs for admin review."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event_log import EventLog
from app.schemas.event_schema import EventSummaryItem, EventSummaryResponse


class EventAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(self, days: int = 7) -> EventSummaryResponse:
        days = max(1, min(days, 90))
        since = datetime.now(timezone.utc) - timedelta(days=days)

        total = (
            self.db.query(func.count(EventLog.id))
            .filter(EventLog.created_at >= since)
            .scalar()
            or 0
        )

        rows = (
            self.db.query(EventLog.event_name, func.count(EventLog.id))
            .filter(EventLog.created_at >= since)
            .group_by(EventLog.event_name)
            .order_by(func.count(EventLog.id).desc())
            .limit(50)
            .all()
        )

        error_names = (
            "code_submit_fail",
            "judge_timeout",
            "judge_fail",
            "ai_analysis_fail",
            "forbidden_access",
            "network_error",
        )
        error_count = sum(count for name, count in rows if name in error_names)

        submit_ok = next((c for n, c in rows if n == "code_submit"), 0)
        submit_fail = next((c for n, c in rows if n == "code_submit_fail"), 0)
        submit_total = submit_ok + submit_fail
        judge_success_rate = round(submit_ok / submit_total * 100, 1) if submit_total else None

        top_events = [EventSummaryItem(event_name=name, count=count) for name, count in rows[:20]]

        return EventSummaryResponse(
            period_days=days,
            total_events=total,
            error_events=error_count,
            judge_success_rate=judge_success_rate,
            top_events=top_events,
        )
