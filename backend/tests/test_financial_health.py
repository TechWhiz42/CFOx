from app.financial_health import calculate_financial_health


def base_comparison(
        *,
        revenue_change=0,
        previous_revenue=1000,
        failure_rate=2,
        failure_change=0,
):
    return {
        "previous_period": {
            "revenue": previous_revenue,
        },
        "current_period": {
            "revenue": previous_revenue + revenue_change,
            "failure_rate": failure_rate,
        },
        "changes": {
            "revenue_change": revenue_change,
            "failure_rate_change_percentage_points": failure_change,
        },
    }


def test_healthy_financial_state():
    result = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=200,
            failure_rate=1,
            failure_change=-1,
        ),
        anomaly={"score": 0, "reasons": []},
        cashflow={"risk_score": 0},
        forecast={
            "recent_average": 80,
            "forecast": [
                {"predicted_revenue": 90},
                {"predicted_revenue": 90},
                {"predicted_revenue": 90},
            ],
        },
    )

    assert result["score"] >= 80
    assert result["status"] == "healthy"


def test_revenue_decline_reduces_health():
    healthy = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=100,
            failure_rate=1,
        ),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    declining = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=-300,
            failure_rate=1,
        ),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    assert declining["score"] < healthy["score"]


def test_payment_failures_reduce_health():
    low_failure = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=0,
            failure_rate=1,
            failure_change=0,
        ),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    high_failure = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=0,
            failure_rate=20,
            failure_change=10,
        ),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    assert high_failure["score"] < low_failure["score"]


def test_cashflow_risk_reduces_health():
    low_risk = calculate_financial_health(
        comparison=base_comparison(),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    high_risk = calculate_financial_health(
        comparison=base_comparison(),
        anomaly={"score": 0},
        cashflow={"risk_score": 100},
    )

    assert high_risk["score"] < low_risk["score"]


def test_anomaly_risk_reduces_health():
    normal = calculate_financial_health(
        comparison=base_comparison(),
        anomaly={"score": 0},
        cashflow={"risk_score": 0},
    )

    risky = calculate_financial_health(
        comparison=base_comparison(),
        anomaly={
            "score": 100,
            "reasons": ["Revenue declined significantly."],
        },
        cashflow={"risk_score": 0},
    )

    assert risky["score"] < normal["score"]


def test_score_is_bounded():
    result = calculate_financial_health(
        comparison=base_comparison(
            revenue_change=-10000,
            failure_rate=100,
            failure_change=100,
        ),
        anomaly={"score": 100},
        cashflow={"risk_score": 100},
    )

    assert 0 <= result["score"] <= 100
