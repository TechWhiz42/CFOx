from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.audit import audit_event
from app.auth import (
    AUTH_COOKIE_NAME,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.models import User
from app.production_hardening import (
    auth_limiter,
    enforce_rate_limit,
    request_rate_limit_key,
)
from app.schemas import (
    LoginResponse,
    UserResponse,
    UserSignup,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _cookie_secure() -> bool:
    return settings.AUTH_COOKIE_SECURE


def _set_auth_cookie(
        response: Response,
        token: str,
) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        max_age=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=_cookie_secure(),
        httponly=True,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
        request: Request,
        payload: UserSignup,
        db: Session = Depends(get_db),
):
    enforce_rate_limit(
        auth_limiter,
        request_rate_limit_key(request, "auth:register"),
    )

    email = payload.email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create account with the provided credentials.",
        )

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    audit_event(
        "auth.registered",
        user_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={
            "email": user.email,
        },
    )

    return user


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    enforce_rate_limit(
        auth_limiter,
        request_rate_limit_key(request, "auth:login"),
    )

    email = form_data.username.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if (
            user is None
            or not verify_password(
        form_data.password,
        user.hashed_password,
    )
    ):
        audit_event(
            "auth.login_failed",
            request_id=getattr(request.state, "request_id", None),
            metadata={
                "email": email,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to authenticate with the provided credentials.",
        )

    token = create_access_token(user.id)

    _set_auth_cookie(
        response,
        token,
    )

    audit_event(
        "auth.login_succeeded",
        user_id=user.id,
        request_id=getattr(request.state, "request_id", None),
    )

    return {
        "status": "authenticated",
    }


@router.post("/logout")
def logout(
        request: Request,
        response: Response,
):
    _clear_auth_cookie(response)

    audit_event(
        "auth.logout",
        request_id=getattr(request.state, "request_id", None),
    )

    return {
        "status": "logged_out",
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
        current_user: User = Depends(get_current_user),
):
    return current_user
