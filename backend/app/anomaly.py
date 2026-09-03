def calculate_anomaly_score(
    failure_rate_change: float,
    failure_rate_multiplier: float | None,
    revenue_change: float
):
    score = 0

    # Failure-rate increase
    if failure_rate_change >= 5:
        score += 30

    if failure_rate_change >= 10:
        score += 20

    # Failure-rate multiplier
    if failure_rate_multiplier is not None:
        if failure_rate_multiplier >= 2:
            score += 20

        if failure_rate_multiplier >= 4:
            score += 10

    # Revenue decline
    if revenue_change < 0:
        score += 10

    if revenue_change <= -100000:
        score += 10

    score = min(score, 100)

    if score >= 70:
        severity = "critical"
    elif score >= 40:
        severity = "warning"
    else:
        severity = "normal"

    return {
        "score": score,
        "severity": severity
    }