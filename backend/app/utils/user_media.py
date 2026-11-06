"""User avatar URL helpers."""

from __future__ import annotations


def avatar_public_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None
    normalized = avatar_path.lstrip("/")
    return f"/api/v1/media/{normalized}"
