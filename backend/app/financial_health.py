from __future__ import annotations


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _number(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _revenue_change_percent(comparison: dict) -> float | None:
    previous = _number(
        comparison.get("previous_period", {}).get("revenue")
    )
    change = _number(
        comparison.get("changes", {}).get("revenue_change")
    )

    if previous <= 0:
        return None

    return (change / previous) * 100.0


def _forecast_change_percent(forecast: dict) -> float | None:
    """
    Compare the seven-day forecast total with the seven-day baseline
    implied by the recent daily average.
    """
    days = forecast.get("forecast")
    if not isinstance(days, list) or not days:
        return None

    predicted_total = sum(
        _number(day.get("predicted_revenue"))
        for day in days
        if isinstance(day, dict)
    )

    recent_average = _number(forecast.get("recent_average"))

    if recent_average <= 0:
        return None

    baseline_total = recent_average * len(days)
    if baseline_total <= 0:
        return None

    return ((predicted_total - baseline_total) / baseline_total) * 100.0


def calculate_financial_health(
    *,
    comparison: dict,
    anomaly: dict,
    cashflow: dict | None = None,
    forecast: dict | None = None,
) -> dict:
    """
    Calculate a deterministic 0-100 financial health score.

    Score components:
      - Revenue trend:       30 points
      - Payment reliability:30 points
      - Cash-flow risk:      25 points
      - Anomaly risk:        15 points

    Higher is healthier.
    """

    cashflow = cashflow or {}
    forecast = forecast or {}

    current = comparison.get("current_period", {})
    changes = comparison.get("changes", {})

    # ---------------------------------------------------------
    # 1. REVENUE HEALTH — 30 points
    # ---------------------------------------------------------
    revenue_change = _revenue_change_percent(comparison)

    if revenue_change is None:
        revenue_score = 15.0
        revenue_status = "insufficient_data"
        revenue_detail = "Previous-period revenue is unavailable."
    elif revenue_change >= 10:
        revenue_score = 30.0
        revenue_status = "strong"
        revenue_detail = "Revenue is growing by at least 10% versus the previous period."
    elif revenue_change >= 0:
        revenue_score = 24.0
        revenue_status = "stable"
        revenue_detail = "Revenue is stable or growing versus the previous period."
    elif revenue_change >= -10:
        revenue_score = 18.0
        revenue_status = "watch"
        revenue_detail = "Revenue has declined, but the decline is below 10%."
    elif revenue_change >= -20:
        revenue_score = 10.0
        revenue_status = "weak"
        revenue_detail = "Revenue has declined by 10% to 20%."
    else:
        revenue_score = 0.0
        revenue_status = "critical"
        revenue_detail = "Revenue has declined by more than 20%."

    # Forecast is a supporting signal, not a replacement for observed revenue.
    forecast_change = _forecast_change_percent(forecast)
    if forecast_change is not None:
        if forecast_change < -20:
            revenue_score -= 6
        elif forecast_change < -10:
            revenue_score -= 3
        elif forecast_change >= 10:
            revenue_score += 2

    revenue_score = _clamp(revenue_score, 0, 30)

    # ---------------------------------------------------------
    # 2. PAYMENT RELIABILITY — 30 points
    # ---------------------------------------------------------
    failure_rate = _number(current.get("failure_rate"))
    failure_change = _number(
        changes.get("failure_rate_change_percentage_points")
    )

    reliability_score = 30.0

    if failure_rate >= 20:
        reliability_score -= 20
    elif failure_rate >= 10:
        reliability_score -= 14
    elif failure_rate >= 5:
        reliability_score -= 8
    elif failure_rate >= 2:
        reliability_score -= 3

    if failure_change >= 10:
        reliability_score -= 8
    elif failure_change >= 5:
        reliability_score -= 5
    elif failure_change >= 2:
        reliability_score -= 2

    reliability_score = _clamp(reliability_score, 0, 30)

    if reliability_score >= 24:
        reliability_status = "strong"
    elif reliability_score >= 16:
        reliability_status = "watch"
    elif reliability_score >= 8:
        reliability_status = "weak"
    else:
        reliability_status = "critical"

    # ---------------------------------------------------------
    # 3. CASH-FLOW HEALTH — 25 points
    # ---------------------------------------------------------
    cashflow_risk_score = _number(
        cashflow.get("risk_score"),
        default=0.0,
    )

    # Existing CFOx cashflow risk score is interpreted as risk:
    # 0 = no measured risk, 100 = highest risk.
    cashflow_score = _clamp(
        25.0 - (cashflow_risk_score * 0.25),
        0,
        25,
    )

    if cashflow_risk_score >= 80:
        cashflow_status = "critical"
    elif cashflow_risk_score >= 50:
        cashflow_status = "weak"
    elif cashflow_risk_score >= 20:
        cashflow_status = "watch"
    else:
        cashflow_status = "strong"

    # ---------------------------------------------------------
    # 4. ANOMALY HEALTH — 15 points
    # ---------------------------------------------------------
    anomaly_score = _clamp(
        _number(anomaly.get("score")),
        0,
        100,
    )

    anomaly_health_score = 15.0 - (anomaly_score * 0.15)

    if anomaly_score >= 70:
        anomaly_status = "critical"
    elif anomaly_score >= 40:
        anomaly_status = "warning"
    elif anomaly_score > 0:
        anomaly_status = "watch"
    else:
        anomaly_status = "normal"

    # ---------------------------------------------------------
    # FINAL SCORE
    # ---------------------------------------------------------
    score = _clamp(
        revenue_score
        + reliability_score
        + cashflow_score
        + anomaly_health_score
    )

    score = round(score, 2)

    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "stable"
    elif score >= 40:
        status = "at_risk"
    else:
        status = "critical"

    components = {
        "revenue": {
            "score": round(revenue_score, 2),
            "max_score": 30,
            "status": revenue_status,
            "change_percent": (
                round(revenue_change, 2)
                if revenue_change is not None
                else None
            ),
            "forecast_change_percent": (
                round(forecast_change, 2)
                if forecast_change is not None
                else None
            ),
        },
        "payment_reliability": {
            "score": round(reliability_score, 2),
            "max_score": 30,
            "status": reliability_status,
            "current_failure_rate": round(failure_rate, 2),
            "failure_rate_change_percentage_points": round(
                failure_change,
                2,
            ),
        },
        "cashflow": {
            "score": round(cashflow_score, 2),
            "max_score": 25,
            "status": cashflow_status,
            "risk_score": round(cashflow_risk_score, 2),
        },
        "anomaly": {
            "score": round(anomaly_health_score, 2),
            "max_score": 15,
            "status": anomaly_status,
            "risk_score": round(anomaly_score, 2),
        },
    }

    strengths: list[str] = []
    concerns: list[str] = []

    if revenue_status in {"strong", "stable"}:
        strengths.append(revenue_detail)
    elif revenue_status != "insufficient_data":
        concerns.append(revenue_detail)

    if reliability_status == "strong":
        strengths.append("Payment reliability is currently within a healthy range.")
    elif reliability_status in {"watch", "weak", "critical"}:
        concerns.append(
            f"Current payment failure rate is {failure_rate:.2f}%."
        )

    if cashflow_status == "strong":
        strengths.append("Cash-flow risk is currently low.")
    elif cashflow_status in {"watch", "weak", "critical"}:
        concerns.append(
            f"Cash-flow risk score is {cashflow_risk_score:.2f}."
        )

    if anomaly_status == "normal":
        strengths.append("No material anomaly risk is currently indicated.")
    elif anomaly_status in {"watch", "warning", "critical"}:
        reasons = anomaly.get("reasons") or []
        if reasons:
            concerns.extend(str(reason) for reason in reasons[:3])
        else:
            concerns.append(
                f"Anomaly risk score is {anomaly_score:.2f}."
            )

    return {
        "score": score,
        "status": status,
        "components": components,
        "strengths": strengths[:4],
        "concerns": concerns[:6],
        "methodology": {
            "revenue_weight": 30,
            "payment_reliability_weight": 30,
            "cashflow_weight": 25,
            "anomaly_weight": 15,
            "score_direction": "higher_is_healthier",
        },
    }