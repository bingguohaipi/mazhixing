"""Display names for users (real name vs nickname)."""

from __future__ import annotations

from app.models.user import User


def public_display_name(user: User | None) -> str:
    """Nickname for public UI; falls back to real name then account."""
    if user is None:
        return "未知"
    nick = (user.nickname or "").strip()
    if nick:
        return nick
    real = (user.display_name or "").strip()
    if real:
        return real
    return user.account
