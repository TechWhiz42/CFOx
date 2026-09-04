from app.decision_intelligence import calculate_decision_intelligence


def test_critical_revenue_and_payment_signals():
    result = calculate_decision_intelligence(
        comparison={
            "previous_period": {"revenue": 1000, "total_transactions": 100},
            "current_period": {"revenue": 800, "total_transactions": 100, "failure_rate": 18},
            "changes": {"revenue_change_percent": -20},
        },
        forecast={"recent_average": 100, "forecast": [{"predicted_revenue": 80},
                                                      {"predicted_revenue": 82},
                                                      {"predicted_revenue": 84}]},
        cashflow={"risk": "low", "risk_score": 20},
        anomaly={"severity": "normal", "score": 10},
    )
    ids = {s["id"] for s in result["signals"]}
    assert "revenue-decline" in ids
    assert "payment-failure-critical" in ids
    assert result["status"] == "critical"


def test_forecast_is_explicitly_separate():
    result = calculate_decision_intelligence(
        comparison={"previous_period": {"revenue": 100, "total_transactions": 100},
                    "current_period": {"revenue": 100, "total_transactions": 100},
                    "changes": {"revenue_change_percent": 0}},
        forecast={"recent_average": 100, "forecast": [{"predicted_revenue": 80}] * 3},
        cashflow={"risk": "low", "risk_score": 10},
        anomaly={"severity": "normal", "score": 0},
    )
    signal = next(s for s in result["signals"] if s["id"] == "forecast-decline")
    assert signal["source"] == "revenue_forecast"
    assert "Forecast values are projections" in result["principles"][1]


def test_stable_data_produces_stable_state():
    result = calculate_decision_intelligence(
        comparison={"previous_period": {"revenue": 100, "total_transactions": 100},
                    "current_period": {"revenue": 102, "total_transactions": 100, "failure_rate": 1},
                    "changes": {"revenue_change_percent": 2}},
        forecast={"recent_average": 100, "forecast": [{"predicted_revenue": 101},
                                                      {"predicted_revenue": 102},
                                                      {"predicted_revenue": 99}]},
        cashflow={"risk": "low", "risk_score": 10},
        anomaly={"severity": "normal", "score": 5},
    )
    assert result["status"] == "stable"
    assert result["signals"] == []
