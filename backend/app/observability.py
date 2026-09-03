import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.reliability import CFOAIServiceError, public_ai_error_detail


logger = logging.getLogger("cfox")


def configure_logging(level: str = "INFO") -> None:
    """Configure application logging without exposing financial payloads."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def install_request_observability(app: FastAPI) -> None:
    """Attach a request ID and log safe request lifecycle metadata."""

    @app.middleware("http")
    async def request_observability(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )

            # Starlette can re-raise an exception after an exception handler
            # has been invoked. Returning the safe response here ensures the
            # request ID is still attached and avoids leaking provider/DB
            # details to clients.
            if isinstance(exc, CFOAIServiceError):
                response = JSONResponse(
                    status_code=503,
                    content={
                        "error": "ai_service_unavailable",
                        "message": public_ai_error_detail(),
                        "request_id": request_id,
                    },
                )
            else:
                response = JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "message": "An unexpected error occurred.",
                        "request_id": request_id,
                    },
                )

            response.headers["X-Request-ID"] = request_id
            return response

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
