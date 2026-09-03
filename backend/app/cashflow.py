from decimal import Decimal

from sqlalchemy.orm import Session

from app.analytics import compare_periods
from app.forecasting import forecast_revenue


def calculate_cashflow_risk(
    db: Session,
    payment_method: str | None = None,
    comparison: dict | None = None,
    forecast: dict | None = None,
    user_id: int | None = None,
):
    """
    Calculate cash-flow risk from existing analytics data when
    available, avoiding duplicate database work in the dashboard.

    Direct callers can omit comparison/forecast and this function
    will calculate them itself.
    """

    if comparison is None:
        comparison = compare_periods(
            db,
            payment_method,
            user_id=user_id,
        )

    if forecast is None:
        forecast = forecast_revenue(
            db,
            history_days=30,
            forecast_days=7,
            user_id=user_id,
        )

    if "error" in forecast:
        return {
            "risk": "unknown",
            "reason": forecast["error"],
        }

    current_revenue = Decimal(
        str(comparison["current_period"]["revenue"])
    )
    previous_revenue = Decimal(
        str(comparison["previous_period"]["revenue"])
    )

    revenue_change_percent = Decimal("0")

    if previous_revenue > 0:
        revenue_change_percent = (
            (current_revenue - previous_revenue)
            / previous_revenue
        ) * Decimal("100")

    failure_rate = Decimal(
        str(comparison["current_period"]["failure_rate"])
    )

    score = 0
    reasons = []

    if revenue_change_percent <= Decimal("-10"):
        score += 30
        reasons.append(
            "Revenue declined by more than 10%."
        )

    if revenue_change_percent <= Decimal("-25"):
        score += 20

    if failure_rate >= Decimal("10"):
        score += 25
        reasons.append(
            "Payment failure rate is above 10%."
        )

    if failure_rate >= Decimal("20"):
        score += 15

    if score >= 70:
        risk = "critical"
    elif score >= 40:
        risk = "high"
    elif score >= 20:
        risk = "medium"
    else:
        risk = "low"

    total_forecast = sum(
        (
            Decimal(str(item["predicted_revenue"]))
            for item in forecast["forecast"]
        ),
        Decimal("0"),
    )

    return {
        "risk": risk,
        "risk_score": min(score, 100),
        "current_period_revenue": float(
            current_revenue.quantize(Decimal("0.01"))
        ),
        "revenue_change_percent": float(
            revenue_change_percent.quantize(Decimal("0.01"))
        ),
        "current_failure_rate": float(failure_rate),
        "expected_7_day_revenue": float(
            total_forecast.quantize(Decimal("0.01"))
        ),
        "reasons": reasons,
    }