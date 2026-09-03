
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Health component scores are normalized to these maximums:
REVENUE_MAX = 30
PAYMENT_RELIABILITY_MAX = 30
CASHFLOW_MAX = 25
ANOMALY_MAX = 15


# Component-score thresholds.
#
# A lower component score means greater financial risk.
REVENUE_CRITICAL_THRESHOLD = 12
REVENUE_WARNING_THRESHOLD = 21

PAYMENT_RELIABILITY_CRITICAL_THRESHOLD = 12
PAYMENT_RELIABILITY_WARNING_THRESHOLD = 21

CASHFLOW_CRITICAL_THRESHOLD = 10
CASHFLOW_WARNING_THRESHOLD = 18

ANOMALY_CRITICAL_THRESHOLD = 6
ANOMALY_WARNING_THRESHOLD = 11


# Metric thresholds used as supporting evidence.
REVENUE_DECLINE_WARNING_PERCENT = -10.0
REVENUE_DECLINE_CRITICAL_PERCENT = -25.0

PAYMENT_FAILURE_WARNING_PERCENT = 5.0
PAYMENT_FAILURE_CRITICAL_PERCENT = 15.0

CASHFLOW_RISK_WARNING_SCORE = 40.0
CASHFLOW_RISK_CRITICAL_SCORE = 70.0

ANOMALY_WARNING_SCORE = 40.0
ANOMALY_CRITICAL_SCORE = 70.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: Any, digits: int = 2) -> float:
    """Convert a numeric value to a rounded float."""
    return round(_to_float(value), digits)


def _component_score(
    components: dict[str, Any],
    name: str,
) -> float:
    """
    Extract a component score from the Financial Health response.

    Expected shape:

        {
            "revenue": {
                "score": 24,
                "max_score": 30,
                ...
            }
        }

    The helper also tolerates a direct numeric value.
    """
    component = components.get(name, 0)

    if isinstance(component, dict):
        return _to_float(component.get("score"))

    return _to_float(component)


def _priority_rank(priority: str) -> int:
    """Return numeric priority rank for deterministic sorting."""
    return {
        "P0": 0,
        "P1": 1,
        "P2": 2,
        "P3": 3,
    }.get(priority, 99)


def _add_action(
    actions: list[dict[str, Any]],
    *,
    action_id: str,
    priority: str,
    severity: str,
    title: str,
    description: str,
    metric: str,
    value: Any,
    action: str,
    evidence: dict[str, Any],
) -> None:
    """
    Add one normalized action to the action list.

    Keeping construction in one place guarantees a stable API contract.
    """
    actions.append(
        {
            "id": action_id,
            "priority": priority,
            "severity": severity,
            "title": title,
            "description": description,
            "metric": metric,
            "value": value,
            "action": action,
            "evidence": evidence,
        }
    )


# ---------------------------------------------------------------------------
# Revenue actions
# ---------------------------------------------------------------------------

def _generate_revenue_action(
    actions: list[dict[str, Any]],
    health_components: dict[str, Any],
    supporting_data: dict[str, Any],
) -> None:
    """Generate an action when revenue health is weak."""

    score = _component_score(health_components, "revenue")

    comparison = supporting_data.get("comparison") or {}
    changes = comparison.get("changes") or {}
    current_period = comparison.get("current_period") or {}
    previous_period = comparison.get("previous_period") or {}

    revenue_change = changes.get("revenue_change")
    revenue_change_percentage = changes.get("revenue_change_percentage")

    if revenue_change_percentage is None:
        current_revenue = _to_float(current_period.get("revenue"))
        previous_revenue = _to_float(previous_period.get("revenue"))

        if previous_revenue != 0:
            revenue_change_percentage = (
                (current_revenue - previous_revenue)
                / previous_revenue
            ) * 100

    revenue_change_percentage = _to_float(revenue_change_percentage)

    # A healthy component should not create an action.
    if (
        score > REVENUE_WARNING_THRESHOLD
        and revenue_change_percentage > REVENUE_DECLINE_WARNING_PERCENT
    ):
        return

    is_critical = (
        score <= REVENUE_CRITICAL_THRESHOLD
        or revenue_change_percentage <= REVENUE_DECLINE_CRITICAL_PERCENT
    )

    if is_critical:
        priority = "P0"
        severity = "critical"
        title = "Revenue decline requires attention"
        description = (
            "Revenue has deteriorated significantly compared with the "
            "previous period. Investigate the drivers before the decline "
            "creates further cash-flow pressure."
        )
    else:
        priority = "P1"
        severity = "warning"
        title = "Revenue is declining"
        description = (
            "Revenue is below the previous period. Review the underlying "
            "payment methods and recent transactions to identify the cause."
        )

    current_revenue = current_period.get("revenue")
    previous_revenue = previous_period.get("revenue")

    _add_action(
        actions,
        action_id="revenue_decline",
        priority=priority,
        severity=severity,
        title=title,
        description=description,
        metric="revenue_change_percentage",
        value=_round(revenue_change_percentage),
        action="Investigate revenue decline",
        evidence={
            "health_component": "revenue",
            "health_score": _round(score),
            "max_score": REVENUE_MAX,
            "current_revenue": _round(current_revenue),
            "previous_revenue": _round(previous_revenue),
            "revenue_change": _round(revenue_change),
            "revenue_change_percentage": _round(
                revenue_change_percentage
            ),
        },
    )


# ---------------------------------------------------------------------------
# Payment reliability actions
# ---------------------------------------------------------------------------

def _generate_payment_action(
    actions: list[dict[str, Any]],
    health_components: dict[str, Any],
    supporting_data: dict[str, Any],
) -> None:
    """Generate an action when payment reliability is weak."""

    score = _component_score(
        health_components,
        "payment_reliability",
    )

    comparison = supporting_data.get("comparison") or {}
    current_period = comparison.get("current_period") or {}

    failure_rate = current_period.get("failure_rate")

    # Some analytics responses may expose failure_rate as a percentage,
    # while others may expose it as a decimal.
    failure_rate_value = _to_float(failure_rate)

    if 0 < failure_rate_value < 1:
        failure_rate_value *= 100

    if (
        score > PAYMENT_RELIABILITY_WARNING_THRESHOLD
        and failure_rate_value < PAYMENT_FAILURE_WARNING_PERCENT
    ):
        return

    is_critical = (
        score <= PAYMENT_RELIABILITY_CRITICAL_THRESHOLD
        or failure_rate_value >= PAYMENT_FAILURE_CRITICAL_PERCENT
    )

    if is_critical:
        priority = "P0"
        severity = "critical"
        title = "Payment reliability is critical"
        description = (
            "A significant share of payments is failing. Investigate "
            "payment-method failures and transaction patterns immediately."
        )
    else:
        priority = "P1"
        severity = "warning"
        title = "Payment failures are elevated"
        description = (
            "Payment failures are above the normal warning threshold. "
            "Review the affected payment methods and recent failures."
        )

    _add_action(
        actions,
        action_id="payment_failures",
        priority=priority,
        severity=severity,
        title=title,
        description=description,
        metric="failure_rate",
        value=_round(failure_rate_value),
        action="Investigate payment failures",
        evidence={
            "health_component": "payment_reliability",
            "health_score": _round(score),
            "max_score": PAYMENT_RELIABILITY_MAX,
            "failure_rate": _round(failure_rate_value),
        },
    )


# ---------------------------------------------------------------------------
# Cash-flow actions
# ---------------------------------------------------------------------------

def _generate_cashflow_action(
    actions: list[dict[str, Any]],
    health_components: dict[str, Any],
    supporting_data: dict[str, Any],
) -> None:
    """Generate an action when cash-flow risk is elevated."""

    score = _component_score(
        health_components,
        "cashflow",
    )

    cashflow = supporting_data.get("cashflow") or {}

    risk_score = cashflow.get("risk_score")
    risk = str(cashflow.get("risk") or "").lower()

    risk_score_value = _to_float(risk_score)

    # If the health engine says cash-flow is healthy and the supporting
    # risk score is unavailable, there is nothing actionable to emit.
    if (
        score > CASHFLOW_WARNING_THRESHOLD
        and risk_score is None
        and risk not in {"high", "critical"}
    ):
        return

    is_critical = (
        score <= CASHFLOW_CRITICAL_THRESHOLD
        or risk_score_value >= CASHFLOW_RISK_CRITICAL_SCORE
        or risk in {"critical", "very_high"}
    )

    is_warning = (
        score <= CASHFLOW_WARNING_THRESHOLD
        or risk_score_value >= CASHFLOW_RISK_WARNING_SCORE
        or risk in {"high", "elevated", "medium_high"}
    )

    if not is_warning and not is_critical:
        return

    if is_critical:
        priority = "P0"
        severity = "critical"
        title = "Cash-flow risk is critical"
        description = (
            "Cash-flow conditions indicate significant financial pressure. "
            "Review inflows, outflows, and near-term liquidity immediately."
        )
    else:
        priority = "P1"
        severity = "warning"
        title = "Cash-flow risk is elevated"
        description = (
            "Cash-flow conditions indicate increased financial pressure. "
            "Review recent inflows and outflows before liquidity tightens."
        )

    _add_action(
        actions,
        action_id="cashflow_risk",
        priority=priority,
        severity=severity,
        title=title,
        description=description,
        metric="cashflow_risk_score",
        value=_round(risk_score_value),
        action="Review cash-flow pressure",
        evidence={
            "health_component": "cashflow",
            "health_score": _round(score),
            "max_score": CASHFLOW_MAX,
            "risk": risk or "unknown",
            "risk_score": _round(risk_score_value),
        },
    )


# ---------------------------------------------------------------------------
# Anomaly actions
# ---------------------------------------------------------------------------

def _generate_anomaly_action(
    actions: list[dict[str, Any]],
    health_components: dict[str, Any],
    supporting_data: dict[str, Any],
) -> None:
    """Generate an action when transaction anomaly risk is elevated."""

    score = _component_score(
        health_components,
        "anomaly",
    )

    anomaly = supporting_data.get("anomaly") or {}

    anomaly_score = anomaly.get("score")
    anomaly_score_value = _to_float(anomaly_score)

    anomaly_count = anomaly.get("anomaly_count")

    if (
        score > ANOMALY_WARNING_THRESHOLD
        and anomaly_score_value < ANOMALY_WARNING_SCORE
    ):
        return

    is_critical = (
        score <= ANOMALY_CRITICAL_THRESHOLD
        or anomaly_score_value >= ANOMALY_CRITICAL_SCORE
    )

    if is_critical:
        priority = "P1"
        severity = "critical"
        title = "Unusual transaction activity detected"
        description = (
            "The anomaly score indicates significant unusual financial "
            "activity. Investigate the affected transactions and patterns."
        )
    else:
        priority = "P2"
        severity = "warning"
        title = "Unusual transaction activity detected"
        description = (
            "The anomaly score is elevated. Review unusual transactions "
            "to determine whether they require attention."
        )

    _add_action(
        actions,
        action_id="transaction_anomalies",
        priority=priority,
        severity=severity,
        title=title,
        description=description,
        metric="anomaly_score",
        value=_round(anomaly_score_value),
        action="Investigate unusual transactions",
        evidence={
            "health_component": "anomaly",
            "health_score": _round(score),
            "max_score": ANOMALY_MAX,
            "anomaly_score": _round(anomaly_score_value),
            "anomaly_count": anomaly_count,
        },
    )


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def generate_financial_actions(
    health: dict[str, Any],
    supporting_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generate deterministic, prioritized financial actions.

    Parameters
    ----------
    health:
        Output from ``calculate_financial_health``.

        Expected structure:

        {
            "score": 72,
            "status": "stable",
            "components": {
                "revenue": {
                    "score": 24,
                    "max_score": 30,
                },
                "payment_reliability": {
                    "score": 25,
                    "max_score": 30,
                },
                "cashflow": {
                    "score": 18,
                    "max_score": 25,
                },
                "anomaly": {
                    "score": 12,
                    "max_score": 15,
                },
            }
        }

    supporting_data:
        Verified analytics used as evidence for the actions.

        Expected keys:

        {
            "comparison": {...},
            "anomaly": {...},
            "cashflow": {...},
            "forecast": {...},
        }

    Returns
    -------
    list[dict]
        Prioritized financial actions.

    Notes
    -----
    The function is intentionally deterministic. It does not call an LLM
    and does not invent financial values.
    """

    if not isinstance(health, dict):
        return []

    if not isinstance(supporting_data, dict):
        supporting_data = {}

    components = health.get("components") or {}

    if not isinstance(components, dict):
        components = {}

    actions: list[dict[str, Any]] = []

    _generate_revenue_action(
        actions,
        components,
        supporting_data,
    )

    _generate_payment_action(
        actions,
        components,
        supporting_data,
    )

    _generate_cashflow_action(
        actions,
        components,
        supporting_data,
    )

    _generate_anomaly_action(
        actions,
        components,
        supporting_data,
    )

    # Highest urgency first.
    #
    # When two actions have the same priority, preserve the deterministic
    # component order established above.
    actions.sort(
        key=lambda item: _priority_rank(
            str(item.get("priority", "P3"))
        )
    )

    return actions