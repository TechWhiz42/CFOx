from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analytics import (
    calculate_period_metrics,
    calculate_anomaly_score,
    compare_payment_methods,
)
from app.cashflow import calculate_cashflow_risk
from app.database import Base
from app.models import Transaction, User


# ---------------------------------------------------------
# Test database
# ---------------------------------------------------------

@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = Session()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def add_transaction(
        db,
        *,
        amount,
        status="success",
        payment_method="upi",
        days_ago=1,
):
    owner = db.query(User).filter(User.email == "financial-test@example.com").one_or_none()
    if owner is None:
        owner = User(
            email="financial-test@example.com",
            hashed_password="test-hash",
            is_active=1,
        )
        db.add(owner)
        db.flush()

    transaction = Transaction(
        razorpay_payment_id=f"test_{id(object())}_{days_ago}_{amount}_{status}",
        amount=Decimal(str(amount)),
        currency="INR",
        status=status,
        payment_method=payment_method,
        customer_id="customer_test",
        user_id=owner.id,
        created_at=datetime.utcnow() - timedelta(days=days_ago),
    )

    db.add(transaction)
    db.commit()

    return transaction


# ---------------------------------------------------------
# calculate_period_metrics
# ---------------------------------------------------------

def test_period_metrics_calculates_revenue_and_failures(db):
    add_transaction(
        db,
        amount="1000.00",
        status="success",
        payment_method="upi",
        days_ago=1,
    )

    add_transaction(
        db,
        amount="500.00",
        status="success",
        payment_method="upi",
        days_ago=2,
    )

    add_transaction(
        db,
        amount="300.00",
        status="failed",
        payment_method="upi",
        days_ago=2,
    )

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    result = calculate_period_metrics(
        db,
        start_date,
        end_date,
        payment_method="upi",
    )

    assert result["total_transactions"] == 3
    assert result["failed_transactions"] == 1

    assert result["revenue"] == pytest.approx(
        1500.00,
        abs=0.01,
    )

    assert result["failure_rate"] == pytest.approx(
        33.33,
        abs=0.01,
    )


# ---------------------------------------------------------
# Payment-method filtering
# ---------------------------------------------------------

def test_payment_method_filtering(db):
    add_transaction(
        db,
        amount="1000.00",
        payment_method="upi",
        days_ago=1,
    )

    add_transaction(
        db,
        amount="2000.00",
        payment_method="card",
        days_ago=1,
    )

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    upi = calculate_period_metrics(
        db,
        start_date,
        end_date,
        payment_method="upi",
    )

    card = calculate_period_metrics(
        db,
        start_date,
        end_date,
        payment_method="card",
    )

    assert upi["revenue"] == pytest.approx(1000.00)
    assert card["revenue"] == pytest.approx(2000.00)


# ---------------------------------------------------------
# Anomaly scoring
# ---------------------------------------------------------

def test_anomaly_score_normal():
    comparison = {
        "current_period": {
            "failure_rate": 4.0,
            "revenue": 1050.0,
        },
        "previous_period": {
            "failure_rate": 3.0,
            "revenue": 1000.0,
        },
        "changes": {
            "failure_rate_change_percentage_points": 1.0,
            "failure_rate_multiplier": 1.2,
            "revenue_change": 5.0,
        },
    }

    result = calculate_anomaly_score(comparison)

    assert result["severity"] == "normal"
    assert result["score"] < 40


def test_anomaly_score_critical():
    comparison = {
        "current_period": {
            "failure_rate": 20.0,
            "revenue": 700.0,
        },
        "previous_period": {
            "failure_rate": 5.0,
            "revenue": 1000.0,
        },
        "changes": {
            "failure_rate_change_percentage_points": 15.0,
            "failure_rate_multiplier": 5.0,
            "revenue_change": -30.0,
        },
    }

    result = calculate_anomaly_score(comparison)

    assert result["severity"] == "critical"
    assert result["score"] >= 70


# ---------------------------------------------------------
# Cash-flow risk
# ---------------------------------------------------------

def test_cashflow_risk_uses_existing_analysis_and_forecast(db):
    comparison = {
        "current_period": {
            "revenue": 700.00,
            "failure_rate": 15.0,
        },
        "previous_period": {
            "revenue": 1000.00,
        },
    }

    forecast = {
        "forecast": [
            {"date": "2026-09-03", "predicted_revenue": 100.00},
            {"date": "2026-09-04", "predicted_revenue": 100.00},
            {"date": "2026-09-05", "predicted_revenue": 100.00},
        ]
    }

    result = calculate_cashflow_risk(
        db,
        payment_method="upi",
        comparison=comparison,
        forecast=forecast,
    )

    assert result["current_period_revenue"] == pytest.approx(700.00)

    assert result["revenue_change_percent"] == pytest.approx(
        -30.00,
        abs=0.01,
    )

    assert result["current_failure_rate"] == pytest.approx(15.0)

    assert result["expected_7_day_revenue"] == pytest.approx(
        300.00
    )

    assert result["risk_score"] >= 40


# ---------------------------------------------------------
# Decimal financial precision
# ---------------------------------------------------------

def test_transaction_amount_preserves_decimal(db):
    transaction = add_transaction(
        db,
        amount="1234.56",
        payment_method="upi",
        days_ago=1,
    )

    db.refresh(transaction)

    assert transaction.amount == Decimal("1234.56")


def test_compare_payment_methods(db):
    # Current period
    add_transaction(
        db,
        amount="1000.00",
        status="success",
        payment_method="upi",
        days_ago=1,
    )

    add_transaction(
        db,
        amount="500.00",
        status="failed",
        payment_method="upi",
        days_ago=2,
    )

    add_transaction(
        db,
        amount="2000.00",
        status="success",
        payment_method="card",
        days_ago=3,
    )

    # Previous period
    add_transaction(
        db,
        amount="800.00",
        status="success",
        payment_method="upi",
        days_ago=20,
    )

    add_transaction(
        db,
        amount="1200.00",
        status="success",
        payment_method="card",
        days_ago=20,
    )

    result = compare_payment_methods(db)

    # All supported methods must exist.
    assert "upi" in result
    assert "card" in result
    assert "netbanking" in result

    # UPI current period.
    assert result["upi"]["current_period"]["total_transactions"] == 2
    assert result["upi"]["current_period"]["failed_transactions"] == 1
    assert result["upi"]["current_period"]["revenue"] == pytest.approx(
        1000.00
    )

    # UPI previous period.
    assert result["upi"]["previous_period"]["total_transactions"] == 1
    assert result["upi"]["previous_period"]["revenue"] == pytest.approx(
        800.00
    )

    # Card current period.
    assert result["card"]["current_period"]["total_transactions"] == 1
    assert result["card"]["current_period"]["revenue"] == pytest.approx(
        2000.00
    )

    # Card previous period.
    assert result["card"]["previous_period"]["total_transactions"] == 1
    assert result["card"]["previous_period"]["revenue"] == pytest.approx(
        1200.00
    )

    # Netbanking has no transactions.
    assert result["netbanking"]["current_period"]["total_transactions"] == 0
    assert result["netbanking"]["previous_period"]["total_transactions"] == 0
