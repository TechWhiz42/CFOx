from app.decision_simulation import SimulationScenario, rank_scenarios, simulate_decisions, simulate_scenario


def baseline():
    return {"revenue": 100000, "failure_rate_pct": 4, "cashflow_risk_score": 35, "anomaly_score": 20}


def test_zero_change_preserves_baseline_values():
    result = simulate_scenario(100000, 4, 35, 20, SimulationScenario("base"))
    assert result["projected"]["revenue"] == 100000
    assert result["projected"]["failure_rate_pct"] == 4
    assert result["classification"] == "SCENARIO"


def test_growth_can_outscore_flat_case():
    results = simulate_decisions(
        baseline(),
        [SimulationScenario("base"), SimulationScenario("growth", 15, 0, 30)],
    )
    assert results["recommended_scenario"] == "growth"
    assert results["scenarios"][0]["rank"] == 1


def test_failure_increase_is_penalized():
    good = simulate_scenario(100000, 4, 35, 20, SimulationScenario("good", 5, 0))
    bad = simulate_scenario(100000, 4, 35, 20, SimulationScenario("bad", 5, 12))
    assert bad["decision_score"] < good["decision_score"]
    assert bad["projected"]["failure_rate_pct"] == 16


def test_ranking_is_descending():
    results = [{"scenario": {"name": "a"}, "decision_score": 40, "risk_level": "high"},
               {"scenario": {"name": "b"}, "decision_score": 80, "risk_level": "low"}]
    ranked = rank_scenarios(results)
    assert [x["scenario"]["name"] for x in ranked] == ["b", "a"]
