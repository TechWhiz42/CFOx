import hashlib
import hmac
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import RazorpayWebhookEvent, Transaction


def verify_razorpay_signature(body: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _payment_from_payload(payload: dict) -> dict | None:
    return (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity")
    )


def process_razorpay_event(
    db: Session,
    *,
    event_id: str,
    event_name: str,
    payload: dict,
    owner_user_id: int,
) -> str:
    """Process one Razorpay event exactly once.

    Ownership is derived from server configuration, never from the webhook
    request. This is appropriate for the single-merchant deployment model
    used by CFOx today; multi-merchant routing can later map Razorpay
    account_id to a CFOx user.
    """
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("event_id is required")
    if len(event_id) > 255:
        raise ValueError("event_id is too long")
    if not isinstance(event_name, str) or not event_name.strip():
        raise ValueError("event_name is required")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    existing = (
        db.query(RazorpayWebhookEvent)
        .filter(RazorpayWebhookEvent.event_id == event_id)
        .first()
    )
    if existing:
        return "duplicate"

    event_record = RazorpayWebhookEvent(
        event_id=event_id,
        event_name=event_name,
        received_at=datetime.utcnow(),
    )
    db.add(event_record)

    payment = _payment_from_payload(payload)

    if payment:
        payment_id = payment.get("id")
        if payment_id:
            transaction = (
                db.query(Transaction)
                .filter(Transaction.razorpay_payment_id == payment_id)
                .first()
            )

            status_map = {
                "payment.captured": "success",
                "payment.failed": "failed",
            }
            new_status = status_map.get(event_name)

            if transaction:
                # Webhook delivery is not guaranteed to be ordered. A later
                # successful capture must not be overwritten by a stale fail.
                if new_status == "success" or transaction.status != "success":
                    transaction.status = new_status or transaction.status
            elif event_name in status_map:
                amount_paise = payment.get("amount")
                amount = (
                    Decimal(str(amount_paise)) / Decimal("100")
                    if amount_paise is not None
                    else Decimal("0")
                )
                method = payment.get("method")
                if method == "netbanking":
                    method = "netbanking"
                elif method not in {"upi", "card", "netbanking"}:
                    method = None

                db.add(
                    Transaction(
                        razorpay_payment_id=payment_id,
                        amount=amount,
                        currency=str(payment.get("currency") or "INR").upper(),
                        status=new_status,
                        payment_method=method,
                        customer_id=(
                            payment.get("email")
                            or payment.get("contact")
                        ),
                        created_at=(
                            datetime.utcfromtimestamp(payment["created_at"])
                            if payment.get("created_at")
                            else datetime.utcnow()
                        ),
                        user_id=owner_user_id,
                    )
                )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A concurrent duplicate event may have won the unique constraint.
        if (
            db.query(RazorpayWebhookEvent)
            .filter(RazorpayWebhookEvent.event_id == event_id)
            .first()
        ):
            return "duplicate"
        raise

    return "processed"
