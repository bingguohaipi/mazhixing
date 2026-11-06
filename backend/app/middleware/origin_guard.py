"""Reject cross-origin mutating requests in production."""

from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings


class OriginGuardMiddleware(BaseHTTPMiddleware):
    MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.debug or request.method not in self.MUTATING:
            return await call_next(request)

        path = request.url.path
        if path.startswith("/health") or path.startswith("/api/v1/events/track"):
            return await call_next(request)

        origin = request.headers.get("origin")
        if not origin:
            return await call_next(request)

        allowed = set(settings.cors_origin_list)
        if origin not in allowed:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "message": "暂无权限访问该页面", "data": None},
            )

        referer = request.headers.get("referer")
        if referer:
            referer_origin = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"
            if referer_origin not in allowed:
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "message": "暂无权限访问该页面", "data": None},
                )

        return await call_next(request)
