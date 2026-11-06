"""Redis-backed rate limiting with in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from app.core.config import get_settings
from app.core.exceptions import AppException

_memory_buckets: dict[str, list[float]] = defaultdict(list)
_memory_lock = Lock()


def _memory_allow(key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    cutoff = now - window_seconds
    with _memory_lock:
        bucket = _memory_buckets[key]
        _memory_buckets[key] = [ts for ts in bucket if ts > cutoff]
        if len(_memory_buckets[key]) >= limit:
            return False
        _memory_buckets[key].append(now)
        return True


def _redis_allow(key: str, limit: int, window_seconds: int) -> bool:
    try:
        import redis

        settings = get_settings()
        client = redis.from_url(settings.celery_broker_url, decode_responses=True)
        redis_key = f"rate:{key}"
        count = client.incr(redis_key)
        if count == 1:
            client.expire(redis_key, window_seconds)
        return count <= limit
    except Exception:  # noqa: BLE001
        return _memory_allow(key, limit, window_seconds)


def check_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """超过窗口内次数上限时抛出 429（优先 Redis，失败回退进程内计数）。"""
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    allowed = _redis_allow(key, limit, window_seconds)
    if not allowed:
        raise AppException(429, "请求过于频繁，请稍后再试", status_code=429)
