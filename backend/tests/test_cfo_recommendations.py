from app.cfo_recommendations import build_cfo_recommendations


def test_critical_health_creates_p0():
    r = build_cfo_recommendations(financial_health={"health": {"score": 30, "status": "critical"}})
    assert r["status"] == "urgent_action"
    assert r["recommendations"][0]["priority"] == "P0"


def test_categories_are_deduplicated():
    r = build_cfo_recommendations(financial_actions={"actions": [
        {"category": "payments", "severity": "warning"},
        {"category": "payments", "severity": "critical"}]})
    assert len(r["recommendations"]) == 1


def test_scenario_is_not_historical():
    r = build_cfo_recommendations(decision_simulation={"recommended_scenario": {"name": "Growth"}})
    assert r["recommendations"][0]["basis"] == "Scenario simulation"
    assert any("not historical" in x.lower() for x in r["principles"])
