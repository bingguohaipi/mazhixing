"""FastAPI dependencies for endpoint rate limiting."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from app.core.deps import get_client_ip
from app.core.rate_limit import check_rate_limit


def _client_ip(request: Request) -> str:
    return get_client_ip(
        request.headers.get("x-forwarded-for"),
        request.headers.get("x-real-ip") or (request.client.host if request.client else None),
    )


def rate_limit_by_ip(prefix: str, limit: int, window_seconds: int) -> Callable[..., None]:
    def _dependency(request: Request) -> None:
        ip = _client_ip(request)
        check_rate_limit(f"{prefix}:ip:{ip}", limit, window_seconds)

    return _dependency


def rate_limit_by_user(prefix: str, limit: int, window_seconds: int) -> Callable[..., None]:
    from app.core.deps import get_current_user
    from app.models.user import User

    def _dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        check_rate_limit(f"{prefix}:user:{current_user.id}", limit, window_seconds)

    return _dependency
