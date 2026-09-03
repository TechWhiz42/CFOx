from app.cfo_reasoning import (
    build_verified_reasoning_context,
    is_follow_up_question,
    serialize_reasoning_context,
)


def test_follow_up_detection():
    assert is_follow_up_question("What about UPI?")
    assert is_follow_up_question("Why did that happen?")
    assert not is_follow_up_question(
        "Show me revenue by payment method."
    )


def test_reasoning_context_extracts_verified_metrics():
    result = build_verified_reasoning_context(
        "get_revenue_analysis",
        {
            "comparison": {
                "previous_period": {"revenue": 100000},
                "current_period": {
                    "revenue": 80000,
                    "failure_rate": 12.5,
                },
                "changes": {
                    "revenue_change": -20000,
                    "failure_rate_change_percentage_points": 4,
                },
            },
            "anomaly": {
                "score": 72,
                "reasons": ["Revenue dropped"],
            },
            "cashflow": {
                "risk": "high",
                "risk_score": 80,
            },
        },
    )

    facts = "\n".join(result["facts"])

    assert "Current-period revenue: $80,000.00." in facts
    assert "Previous-period revenue: $100,000.00." in facts
    assert "Revenue change: $-20,000.00." in facts
    assert "Current-period failure rate: 12.50%." in facts
    assert "Anomaly score: 72." in facts
    assert "Cash-flow risk: high." in facts


def test_revenue_decline_and_failure_increase_are_related():
    result = build_verified_reasoning_context(
        "get_revenue_analysis",
        {
            "comparison": {
                "previous_period": {"revenue": 1000},
                "current_period": {
                    "revenue": 800,
                    "failure_rate": 10,
                },
                "changes": {
                    "revenue_change": -200,
                    "failure_rate_change_percentage_points": 5,
                },
            }
        },
    )

    assert any(
        "revenue declined" in relationship.lower()
        and "failure rate increased" in relationship.lower()
        for relationship in result["relationships"]
    )


def test_payment_method_context_is_deterministic():
    result = build_verified_reasoning_context(
        "compare_payment_methods",
        {
            "payment_methods": {
                "upi": {
                    "current_period": {
                        "revenue": 5000,
                        "failure_rate": 12,
                    },
                    "previous_period": {
                        "revenue": 7000,
                    },
                    "changes": {
                        "failure_rate_change_percentage_points": 3,
                    },
                },
                "card": {
                    "current_period": {
                        "revenue": 9000,
                        "failure_rate": 2,
                    },
                    "previous_period": {
                        "revenue": 8000,
                    },
                    "changes": {},
                },
            }
        },
    )

    assert any("upi" in item.lower() for item in result["facts"])
    assert any(
        "failure rate increased" in item.lower()
        for item in result["relationships"]
    )
    assert any(
        "largest current-period revenue contribution" in item.lower()
        for item in result["relationships"]
    )


def test_serialization_is_valid_json():
    encoded = serialize_reasoning_context(
        "get_revenue_analysis",
        {
            "comparison": {
                "current_period": {"revenue": 1234.5}
            }
        },
    )

    assert '"tool":"get_revenue_analysis"' in encoded
