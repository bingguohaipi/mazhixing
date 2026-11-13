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

        if not self._allow(origin, request):
            return JSONResponse(
                status_code=403,
                content={"code": 403, "message": "暂无权限访问该页面", "data": None},
            )

        referer = request.headers.get("referer")
        if referer:
            referer_origin = f"{urlparse(referer).scheme}://{urlparse(referer).netloc}"
            if not self._allow(referer_origin, request):
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "message": "暂无权限访问该页面", "data": None},
                )

        return await call_next(request)

    @staticmethod
    def _allow(origin: str, request: Request) -> bool:
        """白名单命中，或与当前请求同源（Host 一致）则放行。

        同源放行可以免去把服务器 IP/域名逐个写进 CORS_ORIGINS，
        换机器、换端口也不用改配置。
        """
        if origin in set(get_settings().cors_origin_list):
            return True
        host = (request.headers.get("host") or "").strip().lower()
        if not host:
            return False
        netloc = urlparse(origin).netloc.strip().lower()
        return netloc == host
