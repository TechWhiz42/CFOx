from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)

AUTH_COOKIE_NAME = "cfox_access_token"


def _require_secret_key() -> str:
    if not settings.AUTH_SECRET_KEY:
        raise RuntimeError(
            "AUTH_SECRET_KEY is not configured."
        )

    return settings.AUTH_SECRET_KEY


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
        plain_password: str,
        hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "nbf": now,
        "exp": expires_at,
        "iss": settings.AUTH_ISSUER,
        "aud": settings.AUTH_AUDIENCE,
    }

    return jwt.encode(
        payload,
        _require_secret_key(),
        algorithm=settings.AUTH_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = jwt.decode(
            token,
            _require_secret_key(),
            algorithms=[settings.AUTH_ALGORITHM],
            issuer=settings.AUTH_ISSUER,
            audience=settings.AUTH_AUDIENCE,
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        return int(subject)

    except (JWTError, ValueError, TypeError) as exc:
        raise credentials_exception from exc


def _get_token_from_request(
        request: Request,
        bearer_token: str | None,
) -> str:
    if bearer_token:
        return bearer_token

    cookie_token = request.cookies.get(
        AUTH_COOKIE_NAME
    )

    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
        request: Request,
        token: str | None = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
) -> User:
    access_token = _get_token_from_request(
        request,
        token,
    )

    user_id = decode_access_token(access_token)

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user