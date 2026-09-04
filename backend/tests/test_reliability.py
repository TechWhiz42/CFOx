import hashlib
import hmac
import json

from app import routes
from app.auth import create_access_token, hash_password
from app.models import RazorpayWebhookEvent, User
from app.reliability import CFOAIServiceError


def _auth_client(
        client,
        db,
        email="reliability@example.com",
):
    user = User(
        email=email,
        hashed_password=hash_password(
            "ReliabilityTestPassword123!"
        ),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    client.headers.update(
        {
            "Authorization": (
                f"Bearer {create_access_token(user.id)}"
            )
        }
    )

    return user


def test_request_id_is_generated_and_returned(client):
    response = client.get("/")

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id
    assert len(request_id) == 32


def test_request_id_is_preserved(client):
    request_id = "reliability-test-request-id"

    response = client.get(
        "/",
        headers={
            "X-Request-ID": request_id
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_internal_error_is_safe_and_contains_request_id(
        client,
        db,
        monkeypatch,
):
    _auth_client(
        client,
        db,
        "error-reliability@example.com",
    )

    def broken_dashboard(*args, **kwargs):
        raise RuntimeError(
            "SECRET_DATABASE_DETAILS"
        )

    # Use setattr() rather than routes.get_dashboard_analysis
    # so IDE static analysis does not report an unresolved
    # reference for the dynamically imported route symbol.
    setattr(
        routes,
        "get_dashboard_analysis",
        broken_dashboard,
    )

    response = client.get(
        "/transactions/dashboard",
        params={
            "payment_method": "upi"
        },
        headers={
            "X-Request-ID": "safe-error-request"
        },
    )

    assert response.status_code == 500

    body = response.json()

    assert body["error"] == (
        "internal_server_error"
    )

    assert body["message"] == (
        "An unexpected error occurred."
    )

    assert body["request_id"] == (
        "safe-error-request"
    )

    assert (
            "SECRET_DATABASE_DETAILS"
            not in response.text
    )


def test_legacy_cfo_stream_sanitizes_ai_failure(
        client,
        db,
        monkeypatch,
):
    _auth_client(
        client,
        db,
        "legacy-ai-reliability@example.com",
    )

    def broken_stream(*args, **kwargs):
        raise CFOAIServiceError(
            "OLLAMA_INTERNAL_SECRET"
        )

    # Patch through setattr() to avoid IDE unresolved
    # reference warnings.
    setattr(
        routes,
        "stream_cfo_answer",
        broken_stream,
    )

    response = client.post(
        "/transactions/cfo/chat",
        json={
            "question": "What is my revenue?"
        },
    )

    assert response.status_code == 200

    lines = [
        line
        for line in response.text.splitlines()
        if line.strip()
    ]

    payloads = [
        json.loads(line)
        for line in lines
    ]

    assert payloads[-1] == {
        "type": "error",
        "detail": (
            "CFO analysis is temporarily "
            "unavailable. Please try again."
        ),
    }

    assert (
            "OLLAMA_INTERNAL_SECRET"
            not in response.text
    )


def test_webhook_rejects_non_object_json(client):
    body = b"[]"

    signature = hmac.new(
        b"test-webhook-secret",
        body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": (
                "non-object-payload"
            ),
            "Content-Type": (
                "application/json"
            ),
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Webhook body must contain a JSON object."
    )


def test_webhook_rejects_overlong_event_id(client):
    body = json.dumps(
        {
            "event": "payment.captured"
        }
    ).encode()

    signature = hmac.new(
        b"test-webhook-secret",
        body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": "x" * 256,
            "Content-Type": (
                "application/json"
            ),
        },
    )

    assert response.status_code == 400


def test_webhook_duplicate_event_is_idempotent(
        client,
        db,
):
    event_id = (
        "reliability_duplicate_event_001"
    )

    payload = {
        "id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": (
                        "pay_reliability_duplicate_001"
                    ),
                    "amount": 10000,
                    "currency": "INR",
                    "status": "captured",
                    "method": "upi",
                    "customer_id": (
                        "customer_reliability"
                    ),
                }
            }
        },
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = hmac.new(
        b"test-webhook-secret",
        body,
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "X-Razorpay-Signature": signature,
        "x-razorpay-event-id": event_id,
        "Content-Type": (
            "application/json"
        ),
    }

    first = client.post(
        "/webhooks/razorpay",
        content=body,
        headers=headers,
    )

    second = client.post(
        "/webhooks/razorpay",
        content=body,
        headers=headers,
    )

    assert first.status_code in {
        200,
        201,
    }

    assert second.status_code == 200

    event_count = (
        db.query(RazorpayWebhookEvent)
        .filter(
            RazorpayWebhookEvent.event_id
            == event_id
        )
        .count()
    )

    assert event_count == 1
