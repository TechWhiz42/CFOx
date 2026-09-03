"""
CFOx security regression suite.

These tests intentionally attack the API from the boundary:
- missing/invalid authentication
- cross-user transaction access
- cross-user conversation access
- cross-user conversation mutation
- oversized/invalid inputs
- duplicate transaction ingestion
- webhook signature validation
- safe handling of internal exceptions

The suite builds on the existing test_api.py `client` and `db` fixtures.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.auth import create_access_token, hash_password
from app.models import ChatMessage, Conversation, Transaction, User


# ---------------------------------------------------------------------------
# Security fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def security_client(client, db):
    """
    Create a dedicated authenticated user for security tests.

    We intentionally do not rely on the api-test@example.com user from
    test_api.py. Security tests should create and control their own identity.
    """
    user = User(
        email="security-owner@example.com",
        hashed_password=hash_password("SecurityTestPassword123!"),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    client.headers.update(
        {
            "Authorization": f"Bearer {token}",
        }
    )

    return client, user


def _make_user(db, email: str) -> User:
    """Create an active test user."""
    user = User(
        email=email,
        hashed_password=hash_password("SecurityTestPassword123!"),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def test_protected_financial_endpoint_requires_auth(client):
    """Protected financial endpoints must reject unauthenticated requests."""
    client.headers.pop("Authorization", None)

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "path",
    [
        "/transactions",
        "/transactions/dashboard",
        "/transactions/analytics/payment-methods",
        "/transactions/analytics/anomaly",
        "/transactions/analytics/cashflow-risk",
        "/transactions/analytics/financial-health",
        "/transactions/analytics/financial-actions",
        "/transactions/cfo/conversations",
    ],
)
def test_protected_endpoints_reject_missing_auth(client, path):
    """All important financial endpoints must require authentication."""
    client.headers.pop("Authorization", None)

    response = client.get(path)

    assert response.status_code == 401


def test_invalid_bearer_token_is_rejected(client):
    """Malformed JWTs must not authenticate a request."""
    client.headers["Authorization"] = (
        "Bearer definitely-not-a-valid-jwt"
    )

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Transaction ownership / isolation
# ---------------------------------------------------------------------------

def test_cross_user_transactions_are_not_visible(
    security_client,
    db,
):
    """
    A user must only be able to see their own transactions.
    """
    client, owner = security_client

    other = _make_user(
        db,
        "security-other@example.com",
    )

    now = datetime.utcnow()

    db.add(
        Transaction(
            razorpay_payment_id="security_owner_tx",
            amount=Decimal("100.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            customer_id="owner",
            user_id=owner.id,
            created_at=now - timedelta(days=1),
        )
    )

    db.add(
        Transaction(
            razorpay_payment_id="security_other_tx",
            amount=Decimal("999999.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            customer_id="other",
            user_id=other.id,
            created_at=now - timedelta(days=1),
        )
    )

    db.commit()

    response = client.get(
        "/transactions",
        params={"limit": 100},
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        transaction["razorpay_payment_id"]
        for transaction in data
    }

    assert "security_owner_tx" in ids
    assert "security_other_tx" not in ids


def test_transaction_create_cannot_assign_another_user(
    security_client,
    db,
):
    """
    A client-supplied user_id must never allow assigning a transaction
    to another user.
    """
    client, owner = security_client

    other = _make_user(
        db,
        "transaction-owner-attack@example.com",
    )

    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "security_user_id_attack",
            "amount": "5000.00",
            "currency": "INR",
            "status": "success",
            "payment_method": "upi",
            "customer_id": "security",
            "user_id": other.id,
        },
    )

    # The API should either reject the client-supplied user_id or
    # ignore it and assign the authenticated user's ID.
    assert response.status_code in {201, 422}

    created = (
        db.query(Transaction)
        .filter(
            Transaction.razorpay_payment_id
            == "security_user_id_attack"
        )
        .first()
    )

    if response.status_code == 201:
        assert created is not None
        assert created.user_id == owner.id
        assert created.user_id != other.id
    else:
        assert created is None


def test_duplicate_transaction_does_not_create_second_record(
    security_client,
    db,
):
    """
    Replaying the same payment transaction must not create duplicates.
    """
    client, _ = security_client

    payload = {
        "razorpay_payment_id": "security_duplicate_tx",
        "amount": "1250.00",
        "currency": "INR",
        "status": "success",
        "payment_method": "card",
        "customer_id": "duplicate-test",
    }

    first = client.post(
        "/transactions",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/transactions",
        json=payload,
    )

    assert second.status_code == 409

    count = (
        db.query(Transaction)
        .filter(
            Transaction.razorpay_payment_id
            == "security_duplicate_tx"
        )
        .count()
    )

    assert count == 1


# ---------------------------------------------------------------------------
# Conversation ownership / isolation
# ---------------------------------------------------------------------------

def test_cross_user_conversation_is_not_readable(
    security_client,
    db,
):
    """
    A user must not be able to read another user's conversation.
    """
    client, _ = security_client

    other = _make_user(
        db,
        "conversation-attacker@example.com",
    )

    conversation = Conversation(
        user_id=other.id,
        title="Private financial investigation",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    db.add(
        ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content="PRIVATE FINANCIAL INFORMATION",
        )
    )

    db.commit()

    response = client.get(
        f"/transactions/cfo/conversations/{conversation.id}",
    )

    assert response.status_code == 404
    assert "PRIVATE FINANCIAL INFORMATION" not in response.text


def test_cross_user_conversation_cannot_be_deleted(
    security_client,
    db,
):
    """
    A user must not be able to delete another user's conversation.
    """
    client, _ = security_client

    other = _make_user(
        db,
        "conversation-delete-attacker@example.com",
    )

    conversation = Conversation(
        user_id=other.id,
        title="Do not delete",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    response = client.delete(
        f"/transactions/cfo/conversations/{conversation.id}",
    )

    assert response.status_code == 404

    assert (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation.id
        )
        .first()
        is not None
    )


def test_cross_user_conversation_cannot_receive_message(
    security_client,
    db,
    monkeypatch,
):
    """
    Unauthorized conversation mutation must stop before CFO generation.
    """
    client, _ = security_client

    other = _make_user(
        db,
        "conversation-message-attacker@example.com",
    )

    conversation = Conversation(
        user_id=other.id,
        title="Private conversation",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    called = {"value": False}

    def should_not_run(*args, **kwargs):
        called["value"] = True
        raise AssertionError(
            "CFO generation must not run for an unauthorized conversation."
        )

    from app import cfo_conversation_service

    monkeypatch.setattr(
        cfo_conversation_service,
        "generate_stateful_cfo_answer",
        should_not_run,
    )

    response = client.post(
        f"/transactions/cfo/conversations/{conversation.id}/messages",
        json={"content": "Attack attempt"},
    )

    assert response.status_code == 404
    assert called["value"] is False


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_cfo_question_has_length_validation(
    security_client,
):
    """
    CFO questions above the configured maximum should be rejected.
    """
    client, _ = security_client

    response = client.post(
        "/transactions/cfo/chat",
        json={
            "question": "x" * 2001,
        },
    )

    assert response.status_code == 422


def test_cfo_empty_persistent_message_is_rejected(
    security_client,
):
    """
    Empty/whitespace persistent CFO messages must be rejected.
    """
    client, _ = security_client

    response = client.post(
        "/transactions/cfo/conversations",
        json={"title": "Security test"},
    )

    assert response.status_code == 201

    conversation_id = response.json()["id"]

    response = client.post(
        f"/transactions/cfo/conversations/{conversation_id}/messages",
        json={"content": "   "},
    )

    assert response.status_code in {400, 422}


def test_invalid_payment_method_is_rejected(
    security_client,
):
    """Unsupported payment methods must not reach analytics logic."""
    client, _ = security_client

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "bitcoin"},
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Financial intelligence authentication
# ---------------------------------------------------------------------------

def test_financial_health_requires_auth(client):
    """Financial health must require authentication."""
    client.headers.pop("Authorization", None)

    response = client.get(
        "/transactions/analytics/financial-health",
    )

    assert response.status_code == 401


def test_financial_actions_requires_auth(client):
    """Financial actions must require authentication."""
    client.headers.pop("Authorization", None)

    response = client.get(
        "/transactions/analytics/financial-actions",
    )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Razorpay webhook security
# ---------------------------------------------------------------------------

def test_webhook_rejects_missing_signature(client):
    """
    A webhook without a Razorpay signature must be rejected.

    Depending on environment configuration, the endpoint may return 400
    for invalid input or 503 when the webhook secret is unavailable.
    """
    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={
            "x-razorpay-event-id": (
                "security-webhook-missing-signature"
            ),
        },
    )

    assert response.status_code in {400, 503}


def test_webhook_rejects_invalid_signature(client):
    """An invalid Razorpay signature must never be accepted."""
    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={
            "x-razorpay-event-id": (
                "security-webhook-invalid-signature"
            ),
            "X-Razorpay-Signature": "invalid",
        },
    )

    assert response.status_code in {400, 503}


# ---------------------------------------------------------------------------
# Internal error handling
# ---------------------------------------------------------------------------

def test_internal_errors_are_not_exposed(
    security_client,
    monkeypatch,
):
    """
    Internal exceptions must result in a safe generic response rather
    than leaking implementation/database details to the client.
    """
    client, _ = security_client

    from app import routes

    def broken_dashboard(*args, **kwargs):
        raise RuntimeError(
            "PRIVATE_INTERNAL_DATABASE_INFORMATION"
        )

    dashboard_attribute = (
        "get_" + "dashboard_" + "analysis"
    )

    monkeypatch.setattr(
        routes,
        dashboard_attribute,
        broken_dashboard,
        raising=True,
    )

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 500

    assert (
        "PRIVATE_INTERNAL_DATABASE_INFORMATION"
        not in response.text
    )

    if response.headers.get(
        "content-type",
        "",
    ).startswith("application/json"):
        body = response.json()

        assert body.get("message") == (
            "An unexpected error occurred."
        )