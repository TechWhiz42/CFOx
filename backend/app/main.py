from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth_routes import router as auth_router
from app.config import settings
from app.errors import register_exception_handlers
from app.health import router as health_router
from app.observability import configure_logging, install_request_observability
from app.routes import router, webhook_router

app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
)

configure_logging(getattr(settings, "LOG_LEVEL", "INFO"))
register_exception_handlers(app)
install_request_observability(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Razorpay-Signature",
    ],
)


@app.get("/")
def root():
    return {
        "name": "CFOx",
        "status": "running",
        "health": "/healthz",
        "readiness": "/readyz",
    }


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(router)
app.include_router(webhook_router)