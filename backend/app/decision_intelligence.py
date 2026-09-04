from __future__ import annotations

from typing import Any

SEVERITY_ORDER = {"critical": 0, "warning": 1, "watch": 2, "positive": 3, "normal": 4}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first(mapping: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _revenue_change_percent(comparison: dict[str, Any]) -> float:
    changes = comparison.get("changes") or {}
    value = _first(changes, "revenue_change_percent", "revenue_change_percentage",
                   "revenue_change_pct", default=None)
    if value is not None:
        return _number(value)
    current = _number((comparison.get("current_period") or {}).get("revenue"))
    previous = _number((comparison.get("previous_period") or {}).get("revenue"))
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100.0


def _current_failure_rate(comparison: dict[str, Any]) -> float:
    current = comparison.get("current_period") or {}
    return _number(_first(current, "failure_rate", "failed_rate",
                          "failure_percentage", default=0))


def _forecast_signal(forecast: dict[str, Any]) -> dict[str, Any]:
    points = forecast.get("forecast")
    if not isinstance(points, list):
        points = []
    values = [
        _number(point.get("predicted_revenue"))
        for point in points
        if isinstance(point, dict) and point.get("predicted_revenue") is not None
    ]
    recent_average = _number(forecast.get("recent_average"))
    projected_average = sum(values) / len(values) if values else 0.0
    change_percent = (
        0.0 if recent_average == 0
        else ((projected_average - recent_average) / recent_average) * 100.0
    )
    if change_percent <= -10:
        direction = "declining"
    elif change_percent >= 10:
        direction = "growing"
    else:
        direction = "stable"
    return {
        "direction": direction,
        "projected_average": round(projected_average, 2),
        "recent_average": round(recent_average, 2),
        "change_percent": round(change_percent, 2),
        "forecast_days": len(values),
    }


def _confidence(forecast: dict[str, Any], comparison: dict[str, Any]) -> float:
    points = forecast.get("forecast")
    forecast_points = len(points) if isinstance(points, list) else 0
    current = comparison.get("current_period") or {}
    transaction_count = _number(_first(
        current, "total_transactions", "transactions", "transaction_count", default=0
    ))
    score = 0.55
    if forecast_points >= 7:
        score += 0.15
    elif forecast_points >= 3:
        score += 0.08
    if transaction_count >= 100:
        score += 0.15
    elif transaction_count >= 30:
        score += 0.08
    return round(min(score, 0.9), 2)


def calculate_decision_intelligence(
        *,
        comparison: dict[str, Any],
        forecast: dict[str, Any],
        cashflow: dict[str, Any],
        anomaly: dict[str, Any],
) -> dict[str, Any]:
    revenue_change = _revenue_change_percent(comparison)
    failure_rate = _current_failure_rate(comparison)
    forecast_signal = _forecast_signal(forecast)
    cashflow_score = _number(_first(cashflow, "risk_score", "score", default=0))
    cashflow_risk = str(_first(cashflow, "risk", "status", default="unknown")).lower()
    anomaly_score = _number(_first(anomaly, "score", "risk_score", default=0))
    anomaly_severity = str(_first(anomaly, "severity", "status", default="normal")).lower()
    signals = []

    def add(id, type_, severity, title, description, metric, value, source, action):
        signals.append({
            "id": id, "type": type_, "severity": severity, "title": title,
            "description": description, "metric": metric, "value": round(value, 2),
            "source": source, "recommended_action": action,
        })

    if revenue_change <= -15:
        add("revenue-decline", "risk", "critical", "Revenue is declining materially",
            f"Verified revenue is down {abs(revenue_change):.2f}% versus the comparison period.",
            "revenue_change_percent", revenue_change, "historical_comparison",
            "Investigate the largest contributors to the revenue decline.")
    elif revenue_change <= -5:
        add("revenue-softening", "risk", "warning", "Revenue is softening",
            f"Verified revenue is down {abs(revenue_change):.2f}% versus the comparison period.",
            "revenue_change_percent", revenue_change, "historical_comparison",
            "Review payment-method and transaction-level contributors.")
    elif revenue_change >= 10:
        add("revenue-growth", "opportunity", "positive", "Revenue is growing",
            f"Verified revenue is up {revenue_change:.2f}% versus the comparison period.",
            "revenue_change_percent", revenue_change, "historical_comparison",
            "Identify which verified channels are contributing to the increase.")

    if failure_rate >= 15:
        add("payment-failure-critical", "risk", "critical", "Payment failures require attention",
            f"The verified current failure rate is {failure_rate:.2f}%.",
            "failure_rate", failure_rate, "payment_analytics",
            "Review recent failed transactions and affected payment methods.")
    elif failure_rate >= 5:
        add("payment-failure-warning", "risk", "warning", "Payment failures are elevated",
            f"The verified current failure rate is {failure_rate:.2f}%.",
            "failure_rate", failure_rate, "payment_analytics",
            "Inspect failed transactions before the failure rate increases further.")

    if anomaly_severity == "critical" or anomaly_score >= 75:
        add("anomaly-critical", "risk", "critical", "A significant financial anomaly was detected",
            "The deterministic anomaly engine marked the current signal as critical.",
            "anomaly_score", anomaly_score, "anomaly_detection",
            "Open an evidence-backed investigation before taking corrective action.")
    elif anomaly_severity == "warning" or anomaly_score >= 50:
        add("anomaly-watch", "risk", "warning", "A financial anomaly deserves review",
            "The deterministic anomaly engine detected an elevated signal.",
            "anomaly_score", anomaly_score, "anomaly_detection",
            "Review the verified anomaly evidence and affected metrics.")

    if cashflow_risk in {"critical", "high"} or cashflow_score >= 75:
        add("cashflow-critical", "risk", "critical", "Cash-flow risk is high",
            "The verified cash-flow risk assessment is elevated.",
            "cashflow_risk_score", cashflow_score, "cashflow_analysis",
            "Review cash-flow drivers and prioritize near-term liquidity actions.")
    elif cashflow_risk in {"warning", "medium", "at_risk"} or cashflow_score >= 50:
        add("cashflow-watch", "risk", "warning", "Cash-flow risk deserves monitoring",
            "The verified cash-flow assessment indicates elevated risk.",
            "cashflow_risk_score", cashflow_score, "cashflow_analysis",
            "Monitor near-term cash-flow pressure and review the contributing metrics.")

    if forecast_signal["direction"] == "declining":
        add("forecast-decline", "forecast", "warning", "Revenue forecast points downward",
            f"Forecast average is {abs(forecast_signal['change_percent']):.2f}% below the recent average.",
            "forecast_change_percent", forecast_signal["change_percent"], "revenue_forecast",
            "Treat this as a forecast signal and investigate the verified drivers before acting.")
    elif forecast_signal["direction"] == "growing":
        add("forecast-growth", "forecast", "positive", "Revenue forecast points upward",
            f"Forecast average is {forecast_signal['change_percent']:.2f}% above the recent average.",
            "forecast_change_percent", forecast_signal["change_percent"], "revenue_forecast",
            "Validate the trend against verified recent transactions before relying on it.")

    signals.sort(key=lambda s: (SEVERITY_ORDER.get(s["severity"], 99), s["title"]))
    return {
        "status": (
            "critical" if any(s["severity"] == "critical" for s in signals)
            else "attention" if any(s["severity"] == "warning" for s in signals)
            else "positive" if any(s["severity"] == "positive" for s in signals)
            else "stable"
        ),
        "confidence": _confidence(forecast, comparison),
        "forecast": forecast_signal,
        "signals": signals,
        "principles": [
            "Historical metrics are verified observations.",
            "Forecast values are projections, not facts.",
            "Recommendations identify what to investigate; they do not claim an unverified cause.",
        ],
    }
