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
        """白名单命中，或与当前请求同主机（忽略端口）则放行。

        nginx 的 `proxy_set_header Host $host;` 会把端口剥掉（$host 不含端口），
        所以这里只比较主机名，否则 http://IP:8080 访问时会误判为跨站。
        同源放行也免去把服务器 IP/域名逐个写进 CORS_ORIGINS。
        """
        if origin in set(get_settings().cors_origin_list):
            return True

        origin_host = (urlparse(origin).hostname or "").lower()
        if not origin_host:
            return False

        candidates = []
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            candidates.append(forwarded_host.split(",")[0])
        candidates.append(request.headers.get("host") or "")

        for raw in candidates:
            hostname = (raw or "").strip().lower().split(":")[0]
            if hostname and hostname == origin_host:
                return True
        return False
