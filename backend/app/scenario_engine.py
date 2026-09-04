from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pct(value: float) -> float:
    return round(value, 2)


@dataclass(frozen=True)
class ScenarioAssumptions:
    revenue_change_pct: float = 0.0
    failure_rate_change_pct: float = 0.0
    horizon_days: int = 30

    def normalized(self) -> "ScenarioAssumptions":
        return ScenarioAssumptions(
            revenue_change_pct=max(-100.0, min(200.0, _num(self.revenue_change_pct))),
            failure_rate_change_pct=max(-100.0, min(100.0, _num(self.failure_rate_change_pct))),
            horizon_days=max(7, min(365, int(_num(self.horizon_days, 30)))),
        )


def _forecast_average(forecast: dict[str, Any]) -> float:
    points = forecast.get("points") or forecast.get("forecast") or []
    values = []
    for point in points:
        if isinstance(point, dict):
            value = point.get("revenue", point.get("value", point.get("projected_revenue")))
            if value is not None:
                values.append(_num(value))
    return sum(values) / len(values) if values else _num(forecast.get("average"))


def build_scenario(
        baseline: dict[str, Any],
        assumptions: ScenarioAssumptions,
) -> dict[str, Any]:
    """Pure deterministic scenario calculation. Baseline values are treated as verified."""
    a = assumptions.normalized()
    revenue = _num(baseline.get("current_revenue"))
    failure_rate = _num(baseline.get("failure_rate"))
    cashflow = _num(baseline.get("cashflow"))
    anomaly_score = _num(baseline.get("anomaly_score"))

    projected_revenue = revenue * (1 + a.revenue_change_pct / 100.0)
    projected_failure_rate = max(0.0, failure_rate + a.failure_rate_change_pct)
    projected_cashflow = cashflow * (1 + a.revenue_change_pct / 100.0)

    revenue_delta = projected_revenue - revenue
    failure_delta = projected_failure_rate - failure_rate
    cashflow_delta = projected_cashflow - cashflow

    risk = anomaly_score
    risk += max(0.0, a.failure_rate_change_pct) * 2.0
    risk += max(0.0, -a.revenue_change_pct) * 1.5
    risk -= max(0.0, a.revenue_change_pct) * 0.25
    risk = max(0.0, min(100.0, risk))

    if risk >= 75:
        risk_level = "critical"
    elif risk >= 50:
        risk_level = "warning"
    elif risk >= 25:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "assumptions": asdict(a),
        "baseline": {
            "revenue": _pct(revenue),
            "failure_rate": _pct(failure_rate),
            "cashflow": _pct(cashflow),
            "anomaly_score": _pct(anomaly_score),
        },
        "projected": {
            "revenue": _pct(projected_revenue),
            "failure_rate": _pct(projected_failure_rate),
            "cashflow": _pct(projected_cashflow),
            "risk_score": _pct(risk),
        },
        "delta": {
            "revenue": _pct(revenue_delta),
            "failure_rate": _pct(failure_delta),
            "cashflow": _pct(cashflow_delta),
        },
        "risk": {"score": _pct(risk), "level": risk_level},
        "classification": "SCENARIO",
    }


def compare_scenarios(baseline: dict[str, Any], scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for item in scenarios:
        assumptions = ScenarioAssumptions(**item).normalized()
        results.append(build_scenario(baseline, assumptions))
    return {"classification": "SCENARIO", "scenarios": results}


def build_default_scenarios(baseline: dict[str, Any], horizon_days: int = 30) -> dict[str, Any]:
    scenarios = [
        {"name": "conservative", "revenue_change_pct": -10, "failure_rate_change_pct": 3, "horizon_days": horizon_days},
        {"name": "base", "revenue_change_pct": 0, "failure_rate_change_pct": 0, "horizon_days": horizon_days},
        {"name": "optimistic", "revenue_change_pct": 10, "failure_rate_change_pct": -2, "horizon_days": horizon_days},
    ]
    output = []
    for item in scenarios:
        result = build_scenario(baseline, ScenarioAssumptions(**{k: v for k, v in item.items() if k != "name"}))
        result["name"] = item["name"]
        output.append(result)
    return {"classification": "SCENARIO", "scenarios": output}
