from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import settings


def install_request_size_limit(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_size_limit(request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = 0

            if size > settings.MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "request_too_large",
                        "message": "Request body is too large.",
                    },
                )

        return await call_next(request)