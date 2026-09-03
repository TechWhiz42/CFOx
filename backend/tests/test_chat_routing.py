from app.chat_service import route_question


def test_routes_failed_transactions():
    assert (
        route_question(
            "How many payments failed?"
        )
        == "get_failed_transactions"
    )


def test_routes_failed_transactions_plural():
    assert (
        route_question(
            "Show me the failed transactions"
        )
        == "get_failed_transactions"
    )


def test_routes_anomaly():
    assert (
        route_question(
            "Are there any anomalies?"
        )
        == "get_anomaly_analysis"
    )


def test_routes_unusual_transactions_as_anomaly():
    assert (
        route_question(
            "Did we have any unusual transactions?"
        )
        == "get_anomaly_analysis"
    )


def test_routes_payment_methods():
    assert (
        route_question(
            "Which payment method performs best?"
        )
        == "compare_payment_methods"
    )


def test_routes_upi_payment_analysis():
    assert (
        route_question(
            "How is UPI performing?"
        )
        == "compare_payment_methods"
    )


def test_routes_cashflow():
    assert (
        route_question(
            "Is our cash flow at risk?"
        )
        == "get_cashflow_analysis"
    )


def test_routes_liquidity():
    assert (
        route_question(
            "Are we facing a liquidity problem?"
        )
        == "get_cashflow_analysis"
    )


def test_routes_revenue():
    assert (
        route_question(
            "How is our revenue doing?"
        )
        == "get_revenue_analysis"
    )


def test_routes_forecast():
    assert (
        route_question(
            "What is the revenue forecast?"
        )
        == "get_revenue_analysis"
    )


def test_unknown_question_returns_none():
    assert (
        route_question(
            "What should I focus on today?"
        )
        == "none"
    )


def test_empty_question_returns_none():
    assert route_question("") == "none"


def test_whitespace_question_returns_none():
    assert route_question("   ") == "none"


def test_non_string_question_returns_none():
    assert route_question(None) == "none"


def test_verified_context_does_not_trigger_tool():
    assert (
        route_question(
            """
            Investigate this detected financial anomaly.

            Verified data:
            failure rate increased from 4% to 18%.

            Use only these verified facts.
            """
        )
        == "none"
    )


def test_verified_alert_evidence_does_not_trigger_tool():
    assert (
        route_question(
            """
            Investigate this alert using the verified alert evidence.
            """
        )
        == "none"
    )


def test_failed_transaction_has_priority_over_payment_method():
    assert (
        route_question(
            "Why are failed UPI payments increasing?"
        )
        == "get_failed_transactions"
    )


def test_anomaly_has_priority_over_payment_method():
    assert (
        route_question(
            "Is there an unusual UPI payment anomaly?"
        )
        == "get_anomaly_analysis"
    )