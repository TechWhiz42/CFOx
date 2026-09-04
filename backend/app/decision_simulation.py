"""Deterministic multi-scenario decision simulation for CFOx."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class SimulationScenario:
    name: str
    revenue_change_pct: float = 0.0
    failure_rate_delta_pct: float = 0.0
    horizon_days: int = 30


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def simulate_scenario(
        baseline_revenue: float,
        baseline_failure_rate_pct: float,
        baseline_cashflow_risk_score: float,
        baseline_anomaly_score: float,
        scenario: SimulationScenario,
) -> dict:
    """Return only deterministic scenario-derived values; no LLM involved."""
    horizon = int(_clamp(scenario.horizon_days, 7, 90))
    revenue_delta = float(baseline_revenue) * scenario.revenue_change_pct / 100.0
    projected_revenue = float(baseline_revenue) + revenue_delta
    projected_failure_rate = _clamp(
        float(baseline_failure_rate_pct) + scenario.failure_rate_delta_pct,
        0.0,
        100.0,
    )

    # Revenue upside improves the risk score; materially higher payment failures,
    # anomaly exposure, and cash-flow risk reduce it.
    revenue_component = _clamp(scenario.revenue_change_pct * 1.8, -25.0, 25.0)
    failure_penalty = max(0.0, projected_failure_rate - baseline_failure_rate_pct) * 1.5
    cashflow_delta = scenario.revenue_change_pct * -0.35 + scenario.failure_rate_delta_pct * 0.8
    projected_cashflow_risk = _clamp(
        float(baseline_cashflow_risk_score) + cashflow_delta,
        0.0,
        100.0,
    )
    anomaly_delta = max(0.0, scenario.failure_rate_delta_pct * 2.0 - scenario.revenue_change_pct * 0.25)
    projected_anomaly_score = _clamp(
        float(baseline_anomaly_score) + anomaly_delta,
        0.0,
        100.0,
    )

    decision_score = _clamp(
        70.0
        + revenue_component
        - failure_penalty
        - max(0.0, projected_cashflow_risk - 50.0) * 0.25
        - max(0.0, projected_anomaly_score - 50.0) * 0.20,
        0.0,
        100.0,
    )

    if decision_score >= 80:
        risk = "low"
    elif decision_score >= 65:
        risk = "moderate"
    elif decision_score >= 45:
        risk = "high"
    else:
        risk = "critical"

    confidence = _clamp(0.70 + min(horizon, 90) / 900.0, 0.70, 0.80)

    return {
        "scenario": asdict(scenario),
        "horizon_days": horizon,
        "baseline": {
            "revenue": round(float(baseline_revenue), 2),
            "failure_rate_pct": round(float(baseline_failure_rate_pct), 2),
            "cashflow_risk_score": round(float(baseline_cashflow_risk_score), 2),
            "anomaly_score": round(float(baseline_anomaly_score), 2),
        },
        "projected": {
            "revenue": round(projected_revenue, 2),
            "failure_rate_pct": round(projected_failure_rate, 2),
            "cashflow_risk_score": round(projected_cashflow_risk, 2),
            "anomaly_score": round(projected_anomaly_score, 2),
        },
        "delta": {
            "revenue": round(revenue_delta, 2),
            "failure_rate_pct": round(projected_failure_rate - baseline_failure_rate_pct, 2),
            "cashflow_risk_score": round(projected_cashflow_risk - baseline_cashflow_risk_score, 2),
            "anomaly_score": round(projected_anomaly_score - baseline_anomaly_score, 2),
        },
        "decision_score": round(decision_score, 2),
        "risk_level": risk,
        "confidence": round(confidence, 2),
        "classification": "SCENARIO",
    }


def rank_scenarios(results: Iterable[dict]) -> list[dict]:
    """Rank scenarios by deterministic decision score, then lower risk."""
    risk_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
    ranked = sorted(
        list(results),
        key=lambda x: (-float(x.get("decision_score", 0)), risk_order.get(x.get("risk_level"), 9)),
    )
    for index, result in enumerate(ranked, start=1):
        result["rank"] = index
    return ranked


def simulate_decisions(
        baseline: dict,
        scenarios: Iterable[SimulationScenario],
) -> dict:
    results = [
        simulate_scenario(
            baseline_revenue=baseline["revenue"],
            baseline_failure_rate_pct=baseline["failure_rate_pct"],
            baseline_cashflow_risk_score=baseline["cashflow_risk_score"],
            baseline_anomaly_score=baseline["anomaly_score"],
            scenario=scenario,
        )
        for scenario in scenarios
    ]
    ranked = rank_scenarios(results)
    recommendation = ranked[0] if ranked else None
    return {
        "baseline": baseline,
        "scenarios": ranked,
        "recommended_scenario": recommendation["scenario"]["name"] if recommendation else None,
        "classification": "DECISION_SIMULATION",
        "principles": [
            "All projections are hypothetical scenario outputs, not verified historical facts.",
            "Higher decision score indicates a better modeled risk/upside trade-off.",
            "Use verified financial data as the baseline and reassess when actual results arrive.",
        ],
    }
