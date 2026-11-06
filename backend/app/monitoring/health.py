"""Dependency health checks for /health and monitoring."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings


@dataclass
class DependencyHealth:
    name: str
    ok: bool
    message: str


def check_database(db: Session) -> DependencyHealth:
    try:
        db.execute(text("SELECT 1"))
        return DependencyHealth("database", True, "ok")
    except Exception as exc:  # noqa: BLE001
        return DependencyHealth("database", False, str(exc)[:200])


def check_redis() -> DependencyHealth:
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(settings.celery_broker_url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return DependencyHealth("redis", True, "ok")
    except Exception as exc:  # noqa: BLE001
        return DependencyHealth("redis", False, str(exc)[:200])
