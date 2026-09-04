from sqlalchemy.orm import Session

from app.analytics import (
    calculate_anomaly_score,
    compare_periods,
)
from app.cashflow import calculate_cashflow_risk
from app.forecasting import forecast_revenue


def get_dashboard_analysis(
        db: Session,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """
    Build the complete dashboard analytics payload.

    Coordinates comparison, forecasting, cash-flow risk,
    and anomaly analysis while keeping orchestration out
    of the API routes.
    """

    comparison = compare_periods(
        db,
        payment_method,
        user_id,
    )

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=user_id,
    )

    cashflow = calculate_cashflow_risk(
        db,
        payment_method=payment_method,
        comparison=comparison,
        forecast=forecast,
        user_id=user_id,
    )

    anomaly = calculate_anomaly_score(
        comparison,
    )

    return {
        "analysis": comparison,
        "anomaly": anomaly,
        "forecast": forecast,
        "cashflow": cashflow,
    }


def get_alert_analysis(
        db: Session,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """
    Build the analytics payload required by the
    financial-alert engine.
    """

    comparison = compare_periods(
        db,
        payment_method,
        user_id,
    )

    forecast = forecast_revenue(
        db,
        history_days=30,
        forecast_days=7,
        user_id=user_id,
    )

    cashflow = calculate_cashflow_risk(
        db,
        payment_method=payment_method,
        comparison=comparison,
        forecast=forecast,
        user_id=user_id,
    )

    anomaly = calculate_anomaly_score(
        comparison,
    )

    return {
        "analysis": comparison,
        "cashflow": cashflow,
        "anomaly": anomaly,
    }


def get_ai_insight_data(
        db: Session,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """
    Build the financial-data payload consumed by the
    AI financial-insight service.
    """

    analysis = compare_periods(
        db,
        payment_method,
        user_id,
    )

    return {
        "payment_method": payment_method or "all",
        "previous_period": analysis["previous_period"],
        "current_period": analysis["current_period"],
        "changes": analysis["changes"],
    }


def get_anomaly_analysis(
        db: Session,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """
    Build the deterministic anomaly-analysis payload.
    """

    comparison = compare_periods(
        db,
        payment_method,
        user_id,
    )

    anomaly = calculate_anomaly_score(
        comparison,
    )

    return {
        "payment_method": payment_method or "all",
        "anomaly": anomaly,
    }
