"""Distributed lock to prevent concurrent judging for the same user + problem."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.rate_limit import _memory_allow, _redis_allow


def acquire_judge_lock(user_id: int, problem_id: int, ttl_seconds: int = 30) -> None:
    key = f"judge_lock:{user_id}:{problem_id}"
    settings = get_settings()
    if settings.rate_limit_enabled:
        allowed = _redis_allow(key, 1, ttl_seconds)
    else:
        allowed = _memory_allow(key, 1, ttl_seconds)

    if not allowed:
        raise AppException(429, "上一提交仍在判题中，请稍后再试", status_code=429)
