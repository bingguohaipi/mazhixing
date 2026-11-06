"""Retention cleanup for operation and event logs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit import OperationLog
from app.models.event_log import EventLog


def purge_expired_logs(db: Session) -> dict[str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    op_cutoff = now - timedelta(days=settings.operation_log_retention_days)
    event_cutoff = now - timedelta(days=settings.event_log_retention_days)

    op_deleted = (
        db.query(OperationLog)
        .filter(OperationLog.created_at < op_cutoff)
        .delete(synchronize_session=False)
    )
    event_deleted = (
        db.query(EventLog)
        .filter(EventLog.created_at < event_cutoff)
        .delete(synchronize_session=False)
    )
    db.commit()

    return {"operation_logs": op_deleted, "event_logs": event_deleted}
