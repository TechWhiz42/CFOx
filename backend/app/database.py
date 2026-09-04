from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not configured."
    )

engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.DATABASE_URL.startswith(
        ("postgresql://", "postgres://")
):
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        }
    )

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db():
    """
    Provide a database session for a request.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()