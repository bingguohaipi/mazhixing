"""Scheduled audit / event log retention."""

from __future__ import annotations

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.audit_retention import purge_expired_logs


@celery_app.task(name="audit.purge_expired_logs")
def purge_expired_logs_task() -> dict:
    db = SessionLocal()
    try:
        return purge_expired_logs(db)
    finally:
        db.close()
