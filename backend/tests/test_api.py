from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import User, Transaction


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    user = User(
        email="api-test@example.com",
        hashed_password=hash_password("StrongPassword123"),
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    try:
        test_client = TestClient(
            app,
            raise_server_exceptions=False,
        )
        test_client.headers.update(
            {"Authorization": f"Bearer {token}"}
        )
        yield test_client
    finally:
        app.dependency_overrides.clear()


def test_dashboard_all_payment_methods(client):
    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "all"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "analysis" in data
    assert "anomaly" in data
    assert "forecast" in data
    assert "cashflow" in data

    assert data["analysis"]["payment_method"] == "all"


def test_dashboard_upi(client):
    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["analysis"]["payment_method"] == "upi"


def test_payment_method_analytics(client):
    response = client.get(
        "/transactions/analytics/payment-methods"
    )

    assert response.status_code == 200

    data = response.json()

    assert "upi" in data
    assert "card" in data
    assert "netbanking" in data


def test_revenue_history_all(client):
    response = client.get(
        "/transactions/analytics/revenue-history",
        params={
            "days": 30,
            "payment_method": "all",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["days"] == 30
    assert data["payment_method"] == "all"
    assert "history" in data
    assert len(data["history"]) == 30


def test_cashflow_all(client):
    response = client.get(
        "/transactions/analytics/cashflow-risk",
        params={"payment_method": "all"},
    )

    assert response.status_code == 200


def test_anomaly_all(client):
    response = client.get(
        "/transactions/analytics/anomaly",
        params={"payment_method": "all"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_method"] == "all"
    assert "anomaly" in data


def test_alerts_all(client):
    response = client.get(
        "/transactions/alerts",
        params={"payment_method": "all"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_method"] == "all"


def test_invalid_payment_method(client):
    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "bitcoin"},
    )

    assert response.status_code == 400

    data = response.json()

    assert "payment_method" in data["detail"]


def test_invalid_daily_revenue_days(client):
    response = client.get(
        "/transactions/analytics/daily-revenue",
        params={"days": 0},
    )

    assert response.status_code == 400


def test_invalid_forecast_days(client):
    response = client.get(
        "/transactions/analytics/revenue-forecast",
        params={"forecast_days": 31},
    )

    assert response.status_code == 400


def test_empty_cfo_question(client):
    response = client.post(
        "/transactions/cfo/chat",
        json={"question": "   "},
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Question cannot be empty."


def test_unhandled_exception_returns_safe_500(client, monkeypatch):
    from app import routes

    def broken_dashboard(*args, **kwargs):
        raise RuntimeError(
            "THIS SHOULD NOT BE EXPOSED"
        )

    monkeypatch.setattr(
        routes,
        "get_dashboard_analysis",
        broken_dashboard,
    )

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 500

    data = response.json()

    assert data["error"] == "internal_server_error"
    assert data["message"] == (
        "An unexpected error occurred."
    )

    assert "THIS SHOULD NOT BE EXPOSED" not in response.text


def test_transactions_are_isolated_between_users(client, db):
    """An authenticated user must only see their own financial data."""

    # The client fixture authenticates as api-test@example.com.
    owner = (
        db.query(User)
        .filter(User.email == "api-test@example.com")
        .one()
    )

    other_user = User(
        email="other-user@example.com",
        hashed_password=hash_password("OtherStrongPassword123"),
        is_active=1,
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    now = datetime.utcnow()

    db.add_all([
        Transaction(
            razorpay_payment_id="isolation_owner_success",
            amount=Decimal("1000.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            customer_id="owner",
            user_id=owner.id,
            created_at=now - timedelta(days=1),
        ),
        Transaction(
            razorpay_payment_id="isolation_other_success",
            amount=Decimal("9000.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            customer_id="other",
            user_id=other_user.id,
            created_at=now - timedelta(days=1),
        ),
    ])
    db.commit()

    response = client.get(
        "/transactions/dashboard",
        params={"payment_method": "upi"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["analysis"]["current_period"]["revenue"] == 1000.00
    assert data["analysis"]["current_period"]["total_transactions"] == 1


# =========================================================
# PHASE 6 — TRANSACTION INGESTION
# =========================================================

def test_create_transaction_assigns_authenticated_owner(client, db):
    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "phase6_create_001",
            "amount": "1499.50",
            "currency": "inr",
            "status": "success",
            "payment_method": "UPI",
            "customer_id": "cust_phase6",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["razorpay_payment_id"] == "phase6_create_001"
    assert data["amount"] == "1499.50"
    assert data["currency"] == "INR"
    assert data["payment_method"] == "upi"

    owner = db.query(User).filter(User.email == "api-test@example.com").one()
    stored = db.query(Transaction).filter(
        Transaction.razorpay_payment_id == "phase6_create_001"
    ).one()
    assert stored.user_id == owner.id
    assert data["user_id"] == owner.id


def test_create_transaction_rejects_client_supplied_user_id(client):
    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "phase6_forbidden_owner_001",
            "amount": "100.00",
            "currency": "INR",
            "status": "success",
            "payment_method": "upi",
            "user_id": 999999,
        },
    )

    assert response.status_code == 422
    assert "user_id" in response.text


def test_create_transaction_rejects_duplicate_payment_id(client):
    payload = {
        "razorpay_payment_id": "phase6_duplicate_001",
        "amount": "250.00",
        "currency": "INR",
        "status": "success",
        "payment_method": "card",
    }

    first = client.post("/transactions", json=payload)
    second = client.post("/transactions", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_create_transaction_validates_amount(client):
    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "phase6_invalid_amount_001",
            "amount": "0",
            "currency": "INR",
            "status": "success",
            "payment_method": "upi",
        },
    )

    assert response.status_code == 422


def test_create_transaction_validates_payment_method(client):
    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "phase6_invalid_method_001",
            "amount": "100.00",
            "currency": "INR",
            "status": "success",
            "payment_method": "bitcoin",
        },
    )

    assert response.status_code == 422


def test_create_transaction_validates_status(client):
    response = client.post(
        "/transactions",
        json={
            "razorpay_payment_id": "phase6_invalid_status_001",
            "amount": "100.00",
            "currency": "INR",
            "status": "pending",
            "payment_method": "upi",
        },
    )

    assert response.status_code == 422


def test_list_transactions_is_user_scoped_and_paginated(client, db):
    owner = db.query(User).filter(User.email == "api-test@example.com").one()

    db.add_all([
        Transaction(
            razorpay_payment_id="phase6_list_owner_001",
            amount=Decimal("100.00"),
            currency="INR",
            status="success",
            payment_method="upi",
            user_id=owner.id,
            created_at=datetime.utcnow() - timedelta(minutes=2),
        ),
        Transaction(
            razorpay_payment_id="phase6_list_owner_002",
            amount=Decimal("200.00"),
            currency="INR",
            status="success",
            payment_method="card",
            user_id=owner.id,
            created_at=datetime.utcnow() - timedelta(minutes=1),
        ),
    ])
    db.commit()

    response = client.get("/transactions", params={"limit": 1, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["razorpay_payment_id"] == "phase6_list_owner_002"
    assert all(item["user_id"] == owner.id for item in data)


# =========================================================
# PHASE 9 — ADVANCED FINANCIAL ANALYTICS
# =========================================================

def test_advanced_kpis_endpoint(client, db):
    owner = db.query(User).filter(User.email == "api-test@example.com").one()
    now = datetime.utcnow()
    db.add_all([
        Transaction(razorpay_payment_id="phase9_kpi_success", amount=Decimal("1000.00"), currency="INR",
                    status="success", payment_method="upi", customer_id="c1", user_id=owner.id,
                    created_at=now - timedelta(days=1)),
        Transaction(razorpay_payment_id="phase9_kpi_failed", amount=Decimal("500.00"), currency="INR", status="failed",
                    payment_method="upi", customer_id="c2", user_id=owner.id, created_at=now - timedelta(days=1)),
        Transaction(razorpay_payment_id="phase9_kpi_refund", amount=Decimal("200.00"), currency="INR",
                    status="refunded", payment_method="upi", customer_id="c1", user_id=owner.id,
                    created_at=now - timedelta(days=1)),
    ])
    db.commit()

    response = client.get("/transactions/analytics/advanced-kpis", params={"days": 30, "payment_method": "upi"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 3
    assert data["successful_transactions"] == 1
    assert data["failed_transactions"] == 1
    assert data["refunded_transactions"] == 1
    assert data["gross_revenue"] == 1000.0
    assert data["refunded_amount"] == 200.0
    assert data["net_revenue"] == 800.0


def test_daily_performance_endpoint(client, db):
    owner = db.query(User).filter(User.email == "api-test@example.com").one()
    db.add(Transaction(
        razorpay_payment_id="phase9_daily_001", amount=Decimal("750.00"), currency="INR",
        status="success", payment_method="card", customer_id="daily-customer",
        user_id=owner.id, created_at=datetime.utcnow() - timedelta(hours=2),
    ))
    db.commit()

    response = client.get("/transactions/analytics/daily-performance", params={"days": 7, "payment_method": "card"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 7
    assert any(day["revenue"] == 750.0 for day in data["data"])


def test_customer_concentration_is_user_scoped(client, db):
    owner = db.query(User).filter(User.email == "api-test@example.com").one()
    other = User(email="phase9-other@example.com", hashed_password=hash_password("OtherStrongPassword123"), is_active=1)
    db.add(other)
    db.commit()
    db.refresh(other)

    now = datetime.utcnow()
    db.add_all([
        Transaction(razorpay_payment_id="phase9_cust_owner", amount=Decimal("1000.00"), currency="INR",
                    status="success", payment_method="upi", customer_id="owner-customer", user_id=owner.id,
                    created_at=now - timedelta(days=1)),
        Transaction(razorpay_payment_id="phase9_cust_other", amount=Decimal("9000.00"), currency="INR",
                    status="success", payment_method="upi", customer_id="other-customer", user_id=other.id,
                    created_at=now - timedelta(days=1)),
    ])
    db.commit()

    response = client.get("/transactions/analytics/customer-concentration", params={"days": 30, "top_n": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total_revenue"] == 1000.0
    assert data["customers"][0]["customer_id"] == "owner-customer"


def test_phase9_analytics_validate_parameters(client):
    assert client.get("/transactions/analytics/advanced-kpis", params={"days": 0}).status_code == 400
    assert client.get("/transactions/analytics/daily-performance", params={"days": 366}).status_code == 400
    assert client.get("/transactions/analytics/customer-concentration", params={"top_n": 0}).status_code == 400
