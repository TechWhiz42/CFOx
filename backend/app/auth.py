from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def _require_secret_key() -> str:
    if not settings.AUTH_SECRET_KEY:
        raise RuntimeError(
            "AUTH_SECRET_KEY is not configured."
        )

    return settings.AUTH_SECRET_KEY


def hash_password(password: str) -> str:
    """
    Hash a user password using Argon2.
    """
    return password_hash.hash(password)


def verify_password(
        plain_password: str,
        hashed_password: str,
) -> bool:
    """
    Verify a plaintext password against its Argon2 hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT access token.
    """

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        _require_secret_key(),
        algorithm=settings.AUTH_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """
    Decode and validate a JWT access token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            _require_secret_key(),
            algorithms=[settings.AUTH_ALGORITHM],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        return int(subject)

    except (JWTError, ValueError, TypeError) as exc:
        raise credentials_exception from exc


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from the JWT.
    """

    user_id = decode_access_token(token)

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
                "WWW-Authenticate": "Bearer"
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user
