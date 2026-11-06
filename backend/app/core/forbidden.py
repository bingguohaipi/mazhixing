"""Unified forbidden (403) helper with operation audit log."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.audit import log_access_denied
from app.core.exceptions import AppException


def raise_forbidden(
    db: Session,
    user_id: int | None,
    resource: str,
    detail: str,
    *,
    ip: str | None = None,
    commit: bool = True,
) -> None:
    log_access_denied(db, user_id, ip, f"{resource}:{detail}", commit=commit)
    raise AppException(403, "暂无权限访问该页面", status_code=403)
