from app.scenario_engine import ScenarioAssumptions, build_default_scenarios, build_scenario


def baseline():
    return {"current_revenue": 1000, "failure_rate": 5, "cashflow": 400, "anomaly_score": 20}


def test_revenue_scenario_is_deterministic():
    result = build_scenario(baseline(), ScenarioAssumptions(revenue_change_pct=10))
    assert result["projected"]["revenue"] == 1100.0
    assert result["delta"]["revenue"] == 100.0
    assert result["classification"] == "SCENARIO"


def test_failure_rate_scenario_never_goes_negative():
    result = build_scenario(baseline(), ScenarioAssumptions(failure_rate_change_pct=-20))
    assert result["projected"]["failure_rate"] == 0.0


def test_negative_revenue_increases_risk():
    base = build_scenario(baseline(), ScenarioAssumptions())
    downside = build_scenario(baseline(), ScenarioAssumptions(revenue_change_pct=-20))
    assert downside["risk"]["score"] > base["risk"]["score"]


def test_assumptions_are_clamped():
    a = ScenarioAssumptions(500, -500, 9999).normalized()
    assert a.revenue_change_pct == 200
    assert a.failure_rate_change_pct == -100
    assert a.horizon_days == 365


def test_default_scenarios_have_three_cases():
    result = build_default_scenarios(baseline())
    assert [x["name"] for x in result["scenarios"]] == ["conservative", "base", "optimistic"]
    assert all(x["classification"] == "SCENARIO" for x in result["scenarios"])
