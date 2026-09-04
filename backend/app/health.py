import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = logging.getLogger("cfox.health")

router = APIRouter(
    tags=["Health"],
)


@router.get("/healthz")
def healthz():
    """
    Liveness check.

    This confirms the API process is running.
    It does not check external dependencies.
    """

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/readyz")
def readyz():
    """
    Readiness check.

    This confirms the API can reach required dependencies.
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    except Exception:
        logger.exception("Readiness check failed.")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "unavailable",
            },
        )

    return {
        "status": "ready",
        "database": "ok",
    }