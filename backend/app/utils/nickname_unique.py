"""Platform-wide nickname uniqueness (case-insensitive)."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.user import User


def normalize_nickname_for_storage(nickname: str) -> str:
    return nickname.strip()


def assert_nickname_unique(db: Session, nickname: str, exclude_user_id: int | None = None) -> str:
    """Return trimmed nickname; raise if another active user already uses it."""
    normalized = normalize_nickname_for_storage(nickname)
    if not normalized:
        return normalized

    query = db.query(User.id).filter(
        User.deleted_at.is_(None),
        User.nickname.isnot(None),
        func.lower(User.nickname) == normalized.lower(),
    )
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    if query.first() is not None:
        raise AppException(400, "该昵称已被使用，请换一个")
    return normalized
