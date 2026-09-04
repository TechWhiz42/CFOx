import hashlib
import hmac
import json
from app.models import RazorpayWebhookEvent, Transaction, User
from app.auth import hash_password
from app.config import settings


def payload(event, payment_id="pay_webhook_1", status="captured"):
    return {
        "entity": "event",
        "event": event,
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "amount": 149950,
                    "currency": "INR",
                    "status": status,
                    "method": "upi",
                    "email": "customer@example.com",
                    "created_at": 1700000000,
                }
            }
        },
    }


def sign(body: bytes):
    return hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()


def ensure_owner(db):
    owner = db.query(User).filter(User.email == "webhook-test@example.com").first()
    if not owner:
        owner = User(email="webhook-test@example.com", hashed_password=hash_password("password123"))
        db.add(owner)
        db.commit()
        db.refresh(owner)
    return owner


def test_invalid_signature_rejected(client):
    body = json.dumps(payload("payment.captured")).encode()
    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": "bad", "x-razorpay-event-id": "evt_bad"},
    )
    assert response.status_code == 400


def test_missing_event_id_rejected(client):
    body = json.dumps(payload("payment.captured")).encode()
    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": sign(body)},
    )
    assert response.status_code == 400


def test_captured_webhook_creates_transaction(client, db):
    owner = ensure_owner(db)
    settings.RAZORPAY_WEBHOOK_USER_ID = owner.id

    body = json.dumps(payload("payment.captured")).encode()
    response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": sign(body),
            "x-razorpay-event-id": "evt_capture_1",
        },
    )
    assert response.status_code == 200
    assert response.json()["result"] == "processed"

    transaction = db.query(Transaction).filter(Transaction.razorpay_payment_id == "pay_webhook_1").one()
    assert transaction.user_id == owner.id
    assert transaction.status == "success"
    assert str(transaction.amount) == "1499.50"


def test_duplicate_event_is_idempotent(client, db):
    owner = ensure_owner(db)
    settings.RAZORPAY_WEBHOOK_USER_ID = owner.id

    body = json.dumps(payload("payment.captured", "pay_webhook_dup")).encode()
    headers = {
        "X-Razorpay-Signature": sign(body),
        "x-razorpay-event-id": "evt_duplicate_1",
    }
    assert client.post("/webhooks/razorpay", content=body, headers=headers).status_code == 200
    second = client.post("/webhooks/razorpay", content=body, headers=headers)
    assert second.status_code == 200
    assert second.json()["result"] == "duplicate"
    assert db.query(RazorpayWebhookEvent).filter(RazorpayWebhookEvent.event_id == "evt_duplicate_1").count() == 1
    assert db.query(Transaction).filter(Transaction.razorpay_payment_id == "pay_webhook_dup").count() == 1


def test_failed_then_captured_recovers_same_transaction(client, db):
    owner = ensure_owner(db)
    settings.RAZORPAY_WEBHOOK_USER_ID = owner.id

    failed = json.dumps(payload("payment.failed", "pay_recover")).encode()
    captured = json.dumps(payload("payment.captured", "pay_recover")).encode()

    assert client.post(
        "/webhooks/razorpay",
        content=failed,
        headers={"X-Razorpay-Signature": sign(failed), "x-razorpay-event-id": "evt_failed_recover"},
    ).status_code == 200
    assert client.post(
        "/webhooks/razorpay",
        content=captured,
        headers={"X-Razorpay-Signature": sign(captured), "x-razorpay-event-id": "evt_captured_recover"},
    ).status_code == 200

    transaction = db.query(Transaction).filter(Transaction.razorpay_payment_id == "pay_recover").one()
    assert transaction.status == "success"
