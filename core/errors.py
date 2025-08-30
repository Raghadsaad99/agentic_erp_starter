# core/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, extra=None):
        super().__init__(message)
        self.status_code = status_code
        self.extra = extra or {}

def register_error_handlers(app):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc), "extra": exc.extra}
        )
