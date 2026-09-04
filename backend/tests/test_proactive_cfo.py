from app.proactive_cfo import build_proactive_alerts


def test_critical_health():
    r = build_proactive_alerts(financial_health={"health": {"score": 35, "status": "critical"}})
    assert r["has_critical"] is True


def test_deduplicate():
    r = build_proactive_alerts(financial_health={"health": {"score": 35, "status": "critical"}}, financial_actions={
        "actions": [{"category": "financial_health", "severity": "critical"}]})
    assert len(r["alerts"]) == 1


def test_plan_risk():
    r = build_proactive_alerts(financial_plan={"status": "at_risk"})
    assert r["alerts"][0]["category"] == "financial_plan"


def test_scenario_source():
    r = build_proactive_alerts(decision_simulation={"signals": [{"severity": "warning", "title": "Risk"}]})
    assert r["alerts"][0]["source"] == "scenario_simulation"
