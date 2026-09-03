from app.financial_actions import generate_financial_actions


def make_health(
    revenue=30,
    payment_reliability=30,
    cashflow=25,
    anomaly=15,
):
    return {
        "score": (
            revenue
            + payment_reliability
            + cashflow
            + anomaly
        ),
        "status": "healthy",
        "components": {
            "revenue": {
                "score": revenue,
                "max_score": 30,
            },
            "payment_reliability": {
                "score": payment_reliability,
                "max_score": 30,
            },
            "cashflow": {
                "score": cashflow,
                "max_score": 25,
            },
            "anomaly": {
                "score": anomaly,
                "max_score": 15,
            },
        },
    }


def make_supporting_data(
    revenue_change_percentage=0,
    failure_rate=0,
    cashflow_risk_score=0,
    cashflow_risk="low",
    anomaly_score=0,
):
    return {
        "comparison": {
            "current_period": {
                "revenue": 100000,
                "failure_rate": failure_rate,
            },
            "previous_period": {
                "revenue": 100000,
            },
            "changes": {
                "revenue_change": (
                    100000
                    * revenue_change_percentage
                    / 100
                ),
                "revenue_change_percentage": (
                    revenue_change_percentage
                ),
            },
        },
        "cashflow": {
            "risk_score": cashflow_risk_score,
            "risk": cashflow_risk,
        },
        "anomaly": {
            "score": anomaly_score,
            "anomaly_count": 0,
        },
        "forecast": {},
    }


def test_healthy_financial_state_generates_no_actions():
    health = make_health()

    supporting_data = make_supporting_data()

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert actions == []


def test_critical_revenue_decline_generates_p0_action():
    health = make_health(
        revenue=8,
    )

    supporting_data = make_supporting_data(
        revenue_change_percentage=-30,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "revenue_decline"
    assert action["priority"] == "P0"
    assert action["severity"] == "critical"
    assert action["metric"] == "revenue_change_percentage"
    assert action["value"] == -30
    assert action["action"] == "Investigate revenue decline"


def test_warning_revenue_decline_generates_p1_action():
    health = make_health(
        revenue=20,
    )

    supporting_data = make_supporting_data(
        revenue_change_percentage=-15,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "revenue_decline"
    assert action["priority"] == "P1"
    assert action["severity"] == "warning"


def test_critical_payment_failures_generate_p0_action():
    health = make_health(
        payment_reliability=10,
    )

    supporting_data = make_supporting_data(
        failure_rate=20,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "payment_failures"
    assert action["priority"] == "P0"
    assert action["severity"] == "critical"
    assert action["metric"] == "failure_rate"
    assert action["value"] == 20


def test_warning_payment_failures_generate_p1_action():
    health = make_health(
        payment_reliability=20,
    )

    supporting_data = make_supporting_data(
        failure_rate=8,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "payment_failures"
    assert action["priority"] == "P1"
    assert action["severity"] == "warning"


def test_critical_cashflow_risk_generates_p0_action():
    health = make_health(
        cashflow=8,
    )

    supporting_data = make_supporting_data(
        cashflow_risk_score=80,
        cashflow_risk="critical",
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "cashflow_risk"
    assert action["priority"] == "P0"
    assert action["severity"] == "critical"
    assert action["metric"] == "cashflow_risk_score"
    assert action["value"] == 80


def test_warning_cashflow_risk_generates_p1_action():
    health = make_health(
        cashflow=17,
    )

    supporting_data = make_supporting_data(
        cashflow_risk_score=50,
        cashflow_risk="high",
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "cashflow_risk"
    assert action["priority"] == "P1"
    assert action["severity"] == "warning"


def test_critical_anomaly_risk_generates_p1_action():
    health = make_health(
        anomaly=5,
    )

    supporting_data = make_supporting_data(
        anomaly_score=80,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "transaction_anomalies"
    assert action["priority"] == "P1"
    assert action["severity"] == "critical"
    assert action["metric"] == "anomaly_score"
    assert action["value"] == 80


def test_warning_anomaly_risk_generates_p2_action():
    health = make_health(
        anomaly=10,
    )

    supporting_data = make_supporting_data(
        anomaly_score=50,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    action = actions[0]

    assert action["id"] == "transaction_anomalies"
    assert action["priority"] == "P2"
    assert action["severity"] == "warning"


def test_multiple_actions_are_sorted_by_priority():
    health = make_health(
        revenue=8,
        payment_reliability=10,
        cashflow=17,
        anomaly=10,
    )

    supporting_data = make_supporting_data(
        revenue_change_percentage=-30,
        failure_rate=20,
        cashflow_risk_score=50,
        cashflow_risk="high",
        anomaly_score=50,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 4

    priorities = [
        action["priority"]
        for action in actions
    ]

    assert priorities == [
        "P0",
        "P0",
        "P1",
        "P2",
    ]


def test_action_contains_evidence():
    health = make_health(
        revenue=10,
    )

    supporting_data = make_supporting_data(
        revenue_change_percentage=-30,
    )

    actions = generate_financial_actions(
        health,
        supporting_data,
    )

    assert len(actions) == 1

    evidence = actions[0]["evidence"]

    assert evidence["health_component"] == "revenue"
    assert evidence["health_score"] == 10
    assert evidence["max_score"] == 30
    assert evidence["current_revenue"] == 100000
    assert evidence["previous_revenue"] == 100000
    assert evidence["revenue_change_percentage"] == -30


def test_invalid_health_returns_empty_actions():
    actions = generate_financial_actions(
        None,
        {},
    )

    assert actions == []


def test_invalid_supporting_data_does_not_crash():
    health = make_health(
        revenue=10,
    )

    actions = generate_financial_actions(
        health,
        None,
    )

    assert isinstance(actions, list)