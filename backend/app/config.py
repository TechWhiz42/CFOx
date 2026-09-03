import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Application configuration loaded from environment variables.
    """

    APP_NAME: str = os.getenv(
        "APP_NAME",
        "CFOx API",
    )

    ENVIRONMENT: str = os.getenv(
        "ENVIRONMENT",
        "development",
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "false",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "",
    )

    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173",
        ).split(",")
        if origin.strip()
    ]

    DB_POOL_SIZE: int = int(
        os.getenv(
            "DB_POOL_SIZE",
            "5",
        )
    )

    DB_MAX_OVERFLOW: int = int(
        os.getenv(
            "DB_MAX_OVERFLOW",
            "10",
        )
    )

    DB_POOL_TIMEOUT: int = int(
        os.getenv(
            "DB_POOL_TIMEOUT",
            "30",
        )
    )

    DB_POOL_RECYCLE: int = int(
        os.getenv(
            "DB_POOL_RECYCLE",
            "1800",
        )
    )

    LOG_LEVEL: str = os.getenv(
        "LOG_LEVEL",
        "DEBUG" if DEBUG else "INFO",
    ).strip().upper()

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    AUTH_SECRET_KEY: str = os.getenv(
        "AUTH_SECRET_KEY",
        "",
    )

    AUTH_ALGORITHM: str = os.getenv(
        "AUTH_ALGORITHM",
        "HS256",
    )

    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
            "60",
        )
    )

    # =========================================================
    # RAZORPAY WEBHOOKS
    # =========================================================

    RAZORPAY_WEBHOOK_SECRET: str = os.getenv(
        "RAZORPAY_WEBHOOK_SECRET",
        "",
    )

    # Single-merchant deployment owner. The webhook request itself can never
    # choose the CFOx user that owns an ingested transaction.
    RAZORPAY_WEBHOOK_USER_ID: int = int(
        os.getenv(
            "RAZORPAY_WEBHOOK_USER_ID",
            "0",
        )
    )


settings = Settings()