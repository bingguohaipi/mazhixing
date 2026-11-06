"""Client-side analytics event ingestion."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.event_log import EventLog
from app.models.user import User
from app.schemas.event_schema import EventTrackItem


class EventService:
    ERROR_LOG_RETENTION_DAYS = 30
    OPERATION_LOG_RETENTION_DAYS = 90

    def __init__(self, db: Session):
        self.db = db

    def track_events(
        self,
        user: User | None,
        events: list[EventTrackItem],
        ip: str | None,
    ) -> int:
        role = user.role.value if user else None
        user_id = user.id if user else None

        for event in events:
            self.db.add(
                EventLog(
                    user_id=user_id,
                    user_role=role,
                    event_name=event.event_name,
                    page=event.page,
                    module=event.module,
                    detail=event.detail,
                    ip_address=ip,
                )
            )

        self.db.commit()
        self._purge_old_logs()
        return len(events)

    def _purge_old_logs(self) -> None:
        """Best-effort retention cleanup on write path."""
        now = datetime.now(timezone.utc)
        error_cutoff = now - timedelta(days=self.ERROR_LOG_RETENTION_DAYS)
        event_cutoff = now - timedelta(days=self.ERROR_LOG_RETENTION_DAYS)

        (
            self.db.query(EventLog)
            .filter(EventLog.created_at < event_cutoff)
            .delete(synchronize_session=False)
        )
        self.db.commit()
