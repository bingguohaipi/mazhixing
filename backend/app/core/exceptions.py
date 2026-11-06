from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, dict):
            message = detail.get("message", str(detail))
        else:
            message = str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": message, "data": None},
        )
