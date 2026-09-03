from datetime import datetime, timedelta
from decimal import Decimal

from app import ai_investigation
from app.auth import create_access_token, hash_password
from app.models import Transaction, User


def create_test_user(db, email):
    user = User(
        email=email,
        hashed_password=hash_password("test-password-123"),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def test_classify_investigation():
    assert ai_investigation.classify_investigation(
        "Why did revenue fall?"
    ) == "revenue"

    assert ai_investigation.classify_investigation(
        "Why are payments failing?"
    ) == "failure"

    assert ai_investigation.classify_investigation(
        "Why did refunds increase?"
    ) == "refund"

    assert ai_investigation.classify_investigation(
        "Which payment method is worst?"
    ) == "payment_method"

    assert ai_investigation.classify_investigation(
        "Which customers drive revenue?"
    ) == "customer"


def test_investigation_evidence_is_user_scoped(db):
    owner = create_test_user(
        db,
        "investigation-owner@example.com",
    )

    other = create_test_user(
        db,
        "investigation-other@example.com",
    )

    now = datetime.utcnow()

    db.add_all([
        Transaction(
            razorpay_payment_id="inv_owner",
            amount=Decimal("500.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            customer_id="owner",
            user_id=owner.id,
            created_at=now - timedelta(hours=1),
        ),
        Transaction(
            razorpay_payment_id="inv_other",
            amount=Decimal("9000.00"),
            currency="INR",
            status="success",
            payment_method="card",
            customer_id="other",
            user_id=other.id,
            created_at=now - timedelta(hours=1),
        ),
    ])

    db.commit()

    data = ai_investigation.build_investigation_evidence(
        db,
        "Why did revenue fall?",
        owner.id,
        7,
    )

    assert data["revenue"] == 500.0
    assert data["total_transactions"] == 1

    # The other user's transaction must not be included.
    assert data["revenue"] != 9500.0


def test_investigation_route_uses_verified_evidence(
    monkeypatch,
    client,
    db,
):
    user = create_test_user(
        db,
        "investigation-route@example.com",
    )

    token = create_access_token(user.id)

    client.headers.update({
        "Authorization": f"Bearer {token}",
    })

    captured = {}

    def fake_insight(data):
        captured["data"] = data

        return {
            "summary": "Revenue review completed.",
            "severity": "normal",
            "evidence": [
                "Verified transaction data was analyzed."
            ],
            "impact": "No quantified impact identified.",
            "recommendations": [
                "Continue monitoring revenue."
            ],
        }

    monkeypatch.setattr(
        ai_investigation.ai_service,
        "generate_financial_insight",
        fake_insight,
    )

    response = client.post(
        "/transactions/ai/investigate",
        json={
            "question": "Why did revenue fall?",
            "days": 7,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == "Why did revenue fall?"
    assert body["investigation_type"] == "revenue"
    assert body["period_days"] == 7
    assert body["summary"] == "Revenue review completed."

    assert "evidence_data" in body

    evidence = body["evidence_data"]

    assert evidence["investigation_type"] == "revenue"
    assert evidence["period_days"] == 7
    assert "revenue" in evidence
    assert "total_transactions" in evidence

    # Verify the AI service received the verified evidence directly.
    assert "data" in captured

    ai_input = captured["data"]

    assert ai_input["investigation_type"] == "revenue"
    assert ai_input["period_days"] == 7
    assert "revenue" in ai_input
    assert "total_transactions" in ai_input