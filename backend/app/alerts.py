from typing import Any


def _severity_rank(severity: str) -> int:
    return {
        "critical": 3,
        "warning": 2,
        "normal": 1,
    }.get(severity, 0)


def generate_financial_alerts(
    analysis: dict[str, Any],
    cashflow: dict[str, Any] | None = None,
    anomaly: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate prioritized financial alerts.

    Primary alerts represent distinct business problems.

    Supporting signals provide evidence for those problems.

    No LLM is used.
    """

    current = analysis.get(
        "current_period",
        {},
    )

    previous = analysis.get(
        "previous_period",
        {},
    )

    changes = analysis.get(
        "changes",
        {},
    )

    # =====================================================
    # CORE METRICS
    # =====================================================

    current_revenue = float(
        current.get("revenue", 0)
    )

    previous_revenue = float(
        previous.get("revenue", 0)
    )

    failure_rate = float(
        current.get("failure_rate", 0)
    )

    failure_rate_change = float(
        changes.get(
            "failure_rate_change_percentage_points",
            0,
        )
    )

    if previous_revenue > 0:
        revenue_change_percent = round(
            (
                (current_revenue - previous_revenue)
                / previous_revenue
            )
            * 100,
            2,
        )
    else:
        revenue_change_percent = 0.0

    # =====================================================
    # PRIMARY ALERTS
    # =====================================================

    primary_alerts: list[dict[str, Any]] = []

    # -----------------------------------------------------
    # 1. REVENUE DETERIORATION
    # -----------------------------------------------------

    if revenue_change_percent <= -20:
        primary_alerts.append(
            {
                "id": "revenue_deterioration",
                "severity": "critical",
                "title": "Revenue deterioration",
                "message": (
                    f"Revenue declined by "
                    f"{abs(revenue_change_percent):.2f}% "
                    f"compared with the previous period."
                ),
                "metric": "revenue_change_percent",
                "value": revenue_change_percent,
                "threshold": -20,
                "recommended_action": (
                    "Investigate the primary drivers "
                    "of the revenue decline."
                ),
                "evidence": [],
            }
        )

    elif revenue_change_percent <= -10:
        primary_alerts.append(
            {
                "id": "revenue_deterioration",
                "severity": "warning",
                "title": "Revenue deterioration",
                "message": (
                    f"Revenue declined by "
                    f"{abs(revenue_change_percent):.2f}% "
                    f"compared with the previous period."
                ),
                "metric": "revenue_change_percent",
                "value": revenue_change_percent,
                "threshold": -10,
                "recommended_action": (
                    "Review revenue drivers and "
                    "identify the source of the decline."
                ),
                "evidence": [],
            }
        )

    # -----------------------------------------------------
    # 2. PAYMENT SYSTEM DEGRADATION
    # -----------------------------------------------------

    payment_severity = None

    if (
        failure_rate >= 20
        or failure_rate_change >= 10
    ):
        payment_severity = "critical"

    elif (
        failure_rate >= 10
        or failure_rate_change >= 5
    ):
        payment_severity = "warning"

    if payment_severity:
        primary_alerts.append(
            {
                "id": "payment_system_degradation",
                "severity": payment_severity,
                "title": "Payment system degradation",
                "message": (
                    f"Payment failure rate is "
                    f"{failure_rate:.2f}%"
                    f"{f', up {failure_rate_change:.2f} percentage points' if failure_rate_change > 0 else ''}."
                ),
                "metric": "failure_rate",
                "value": failure_rate,
                "threshold": (
                    20
                    if payment_severity == "critical"
                    else 10
                ),
                "recommended_action": (
                    "Investigate payment failures "
                    "and affected payment methods."
                ),
                "evidence": [],
            }
        )

    # -----------------------------------------------------
    # 3. CASH-FLOW EXPOSURE
    # -----------------------------------------------------

    if cashflow:
        risk = str(
            cashflow.get(
                "risk",
                "",
            )
        ).lower()

        risk_score = float(
            cashflow.get(
                "risk_score",
                0,
            )
        )

        cashflow_severity = None

        if (
            risk == "critical"
            or risk_score >= 80
        ):
            cashflow_severity = "critical"

        elif (
            risk == "warning"
            or risk_score >= 50
        ):
            cashflow_severity = "warning"

        if cashflow_severity:
            primary_alerts.append(
                {
                    "id": "cashflow_exposure",
                    "severity": cashflow_severity,
                    "title": "Cash-flow exposure",
                    "message": (
                        f"Cash-flow risk score is "
                        f"{risk_score:.0f}/100."
                    ),
                    "metric": "cashflow_risk_score",
                    "value": risk_score,
                    "threshold": (
                        80
                        if cashflow_severity == "critical"
                        else 50
                    ),
                    "recommended_action": (
                        "Review liquidity exposure and "
                        "address the underlying financial risks."
                    ),
                    "evidence": [],
                }
            )

    # =====================================================
    # SUPPORTING SIGNALS
    # =====================================================

    supporting_signals: list[dict[str, Any]] = []

    # -----------------------------------------------------
    # FAILURE RATE SPIKE
    # -----------------------------------------------------

    if failure_rate_change >= 10:
        supporting_signals.append(
            {
                "id": "failure_rate_spike",
                "severity": "critical",
                "title": "Payment failures increased sharply",
                "message": (
                    f"Failure rate increased by "
                    f"{failure_rate_change:.2f} "
                    f"percentage points."
                ),
                "metric": (
                    "failure_rate_change_percentage_points"
                ),
                "value": failure_rate_change,
            }
        )

    elif failure_rate_change >= 5:
        supporting_signals.append(
            {
                "id": "failure_rate_spike",
                "severity": "warning",
                "title": "Payment failures are increasing",
                "message": (
                    f"Failure rate increased by "
                    f"{failure_rate_change:.2f} "
                    f"percentage points."
                ),
                "metric": (
                    "failure_rate_change_percentage_points"
                ),
                "value": failure_rate_change,
            }
        )

    # -----------------------------------------------------
    # COMBINED REVENUE + PAYMENT SIGNAL
    # -----------------------------------------------------

    if (
        revenue_change_percent <= -10
        and failure_rate >= 10
    ):
        supporting_signals.append(
            {
                "id": "combined_financial_risk",
                "severity": "critical",
                "title": "Revenue and payment risk are correlated",
                "message": (
                    f"Revenue declined by "
                    f"{abs(revenue_change_percent):.2f}% "
                    f"while payment failure rate is "
                    f"{failure_rate:.2f}%."
                ),
                "metric": "combined_risk",
                "value": {
                    "revenue_change_percent":
                        revenue_change_percent,
                    "failure_rate":
                        failure_rate,
                },
            }
        )

    # -----------------------------------------------------
    # ANOMALY SIGNAL
    # -----------------------------------------------------

    if anomaly:
        anomaly_score = float(
            anomaly.get(
                "score",
                0,
            )
        )

        anomaly_severity = str(
            anomaly.get(
                "severity",
                "normal",
            )
        ).lower()

        if (
            anomaly_score >= 50
            or anomaly_severity
            in {
                "warning",
                "critical",
            }
        ):
            supporting_signals.append(
                {
                    "id": "financial_anomaly",
                    "severity": (
                        "critical"
                        if anomaly_score >= 80
                        or anomaly_severity == "critical"
                        else "warning"
                    ),
                    "title": "Financial anomaly detected",
                    "message": (
                        f"CFOx detected an anomaly "
                        f"with a risk score of "
                        f"{anomaly_score:.0f}/100."
                    ),
                    "metric": "anomaly_score",
                    "value": anomaly_score,
                }
            )

    # =====================================================
    # ATTACH EVIDENCE TO PRIMARY ALERTS
    # =====================================================

    for primary in primary_alerts:
        primary_id = primary["id"]

        if primary_id == "revenue_deterioration":
            primary["evidence"] = [
                {
                    "label": "Revenue change",
                    "value": (
                        f"{revenue_change_percent:.2f}%"
                    ),
                },
                {
                    "label": "Previous revenue",
                    "value": previous_revenue,
                },
                {
                    "label": "Current revenue",
                    "value": current_revenue,
                },
            ]

        elif primary_id == "payment_system_degradation":
            primary["evidence"] = [
                {
                    "label": "Current failure rate",
                    "value": failure_rate,
                },
                {
                    "label": "Failure rate change",
                    "value": failure_rate_change,
                },
            ]

        elif primary_id == "cashflow_exposure":
            primary["evidence"] = [
                {
                    "label": "Risk score",
                    "value": cashflow.get(
                        "risk_score",
                        0,
                    ),
                },
                {
                    "label": "Revenue change",
                    "value": cashflow.get(
                        "revenue_change_percent",
                        0,
                    ),
                },
                {
                    "label": "Failure rate",
                    "value": cashflow.get(
                        "current_failure_rate",
                        0,
                    ),
                },
            ]

    # =====================================================
    # SORT
    # =====================================================

    primary_alerts.sort(
        key=lambda alert: _severity_rank(
            alert["severity"]
        ),
        reverse=True,
    )

    supporting_signals.sort(
        key=lambda signal: _severity_rank(
            signal["severity"]
        ),
        reverse=True,
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    critical_count = sum(
        1
        for alert in primary_alerts
        if alert["severity"] == "critical"
    )

    warning_count = sum(
        1
        for alert in primary_alerts
        if alert["severity"] == "warning"
    )

    if critical_count:
        overall_status = "critical"
    elif warning_count:
        overall_status = "warning"
    else:
        overall_status = "normal"

    return {
        "status": overall_status,
        "total_alerts": len(
            primary_alerts
        ),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "primary_alerts": primary_alerts,
        "supporting_signals": supporting_signals,
    }