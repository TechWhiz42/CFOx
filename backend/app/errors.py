import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.reliability import CFOAIServiceError


logger = logging.getLogger("cfox")


def _request_id(request: Request) -> str | None:
    return getattr(
        request.state,
        "request_id",
        None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(CFOAIServiceError)
    async def ai_service_error_handler(
            request: Request,
            exc: CFOAIServiceError,
    ):
        request_id = _request_id(request)

        logger.warning(
            "cfo_ai_failure request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
            exc_info=True,
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "ai_service_unavailable",
                "message": (
                    "CFO analysis is temporarily unavailable. "
                    "Please try again."
                ),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
            request: Request,
            exc: Exception,
    ):
        request_id = _request_id(request)

        # This is intentionally logged with the COMPLETE traceback.
        logger.exception(
            "Unhandled exception request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
            exc,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
            },
        )