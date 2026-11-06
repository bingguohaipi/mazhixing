"""Student fields exposed to teachers (read-only identity)."""

from __future__ import annotations

from app.models.user import User
from app.utils.user_display import public_display_name


def student_identity_fields(user: User) -> dict[str, str | None]:
    return {
        "real_name": user.display_name,
        "nickname": user.nickname,
        "display_name": public_display_name(user),
        "account": user.account,
    }
