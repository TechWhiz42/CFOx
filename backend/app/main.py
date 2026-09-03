from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth_routes import router as auth_router
from app.config import settings
from app.errors import register_exception_handlers
from app.routes import router, webhook_router


app = FastAPI(
    title=settings.APP_NAME,
)


register_exception_handlers(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "CFOx",
        "status": "running",
        "docs": "/docs",
    }


app.include_router(auth_router)
app.include_router(router)
app.include_router(webhook_router)