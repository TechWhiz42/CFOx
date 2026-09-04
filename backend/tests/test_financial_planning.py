from app.financial_planning import build_financial_plan


def test_revenue_gap_and_pace():
    r = build_financial_plan(current_revenue=8000, target_revenue=10000, horizon_days=20)
    assert r["gaps"]["revenue"] == 2000
    assert r["required_pace"]["daily_revenue"] == 100


def test_achieved():
    r = build_financial_plan(current_revenue=12000, target_revenue=10000, current_failure_rate=2, max_failure_rate=5)
    assert r["status"] == "achieved"


def test_failure_risk():
    r = build_financial_plan(current_revenue=10000, target_revenue=10000, current_failure_rate=18, max_failure_rate=10)
    assert r["status"] == "at_risk"
    assert r["failure_rate"]["status"] == "above_limit"


def test_target_is_not_forecast():
    r = build_financial_plan(current_revenue=100, target_revenue=200)
    assert any("not a forecast" in x.lower() for x in r["principles"])
