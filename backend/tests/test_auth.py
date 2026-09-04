from app.auth import create_access_token
from app.auth import (
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User


def test_password_hashing():
    password = "CorrectHorseBatteryStaple"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(
        password,
        hashed,
    )

    assert not verify_password(
        "wrong-password",
        hashed,
    )


def test_create_and_decode_access_token():
    token = create_access_token(123)

    assert isinstance(token, str)
    assert token

    user_id = decode_access_token(token)

    assert user_id == 123


def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "cfo@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "cfo@example.com"
    assert data["id"] > 0
    assert data["is_active"] == 1
    assert "hashed_password" not in data


def test_duplicate_registration(client):
    client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "AnotherPassword123",
        },
    )

    assert response.status_code == 400


def test_login(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "authenticated"
    assert "access_token" not in data


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_authenticated_user(client, db):
    client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "password": "StrongPassword123",
        },
    )

    from app.models import User

    user = (
        db.query(User)
        .filter(User.email == "me@example.com")
        .first()
    )

    token = create_access_token(user.id)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "me@example.com"


def test_financial_endpoint_requires_authentication(client):
    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_financial_endpoint_accepts_valid_token(client,db):
    client.post(
        "/auth/register",
        json={
            "email": "protected@example.com",
            "password": "StrongPassword123",
        },
    )

    user = (
        db.query(User)
        .filter(User.email == "protected@example.com")
        .first()
    )

    token = create_access_token(user.id)

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/transactions/dashboard",
        headers={
            "Authorization": "Bearer definitely-invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_missing_subject_token_is_rejected(client, monkeypatch):
    from app import auth

    def fake_decode(*args, **kwargs):
        raise auth.HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    monkeypatch.setattr(
        auth,
        "decode_access_token",
        fake_decode,
    )

    response = client.get(
        "/transactions/dashboard",
    )

    assert response.status_code == 401


def test_expired_access_token_is_rejected(client):
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    expired = jwt.encode(
        {
            "sub": "123",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "nbf": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iss": settings.AUTH_ISSUER,
            "aud": settings.AUTH_AUDIENCE,
        },
        settings.AUTH_SECRET_KEY,
        algorithm=settings.AUTH_ALGORITHM,
    )

    response = client.get(
        "/transactions/dashboard",
        headers={
            "Authorization": f"Bearer {expired}",
        },
    )

    assert response.status_code == 401

def test_login_sets_http_only_cookie(client):
    client.post(
        "/auth/register",
        json={
            "email": "cookie@example.com",
            "password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "cookie@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 200

    set_cookie = response.headers.get("set-cookie", "")

    assert "cfox_access_token=" in set_cookie
    assert "HttpOnly" in set_cookie


def test_me_accepts_auth_cookie(client):
    client.post(
        "/auth/register",
        json={
            "email": "cookie-me@example.com",
            "password": "StrongPassword123",
        },
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "cookie-me@example.com",
            "password": "StrongPassword123",
        },
    )

    assert login_response.status_code == 200

    response = client.get("/auth/me")

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "cookie-me@example.com"


def test_logout_clears_auth_cookie(client):
    client.post(
        "/auth/register",
        json={
            "email": "logout-cookie@example.com",
            "password": "StrongPassword123",
        },
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "logout-cookie@example.com",
            "password": "StrongPassword123",
        },
    )

    assert login_response.status_code == 200

    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200

    set_cookie = logout_response.headers.get("set-cookie", "")

    assert "cfox_access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie