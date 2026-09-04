from typing import Any


def build_financial_plan(*, current_revenue: float, target_revenue: float,
                         current_cashflow: float = 0.0, target_cashflow: float | None = None,
                         current_failure_rate: float = 0.0, max_failure_rate: float | None = None,
                         horizon_days: int = 30) -> dict[str, Any]:
    horizon_days = max(1, min(int(horizon_days), 3650))
    revenue = float(current_revenue);
    target = float(target_revenue)
    cashflow = float(current_cashflow);
    failure = float(current_failure_rate)
    target_cf = None if target_cashflow is None else float(target_cashflow)
    max_failure = None if max_failure_rate is None else float(max_failure_rate)
    gap = target - revenue
    progress = 100.0 if target <= 0 and revenue >= target else max(0.0, min(100.0,
                                                                            revenue / target * 100.0)) if target > 0 else 0.0
    cf_gap = None if target_cf is None else target_cf - cashflow
    status = "on_track"
    if progress < 50 or (cf_gap is not None and cf_gap > 0): status = "at_risk"
    if max_failure is not None and failure > max_failure: status = "at_risk"
    if revenue >= target and (target_cf is None or cashflow >= target_cf) and (
            max_failure is None or failure <= max_failure):
        status = "achieved"
    return {
        "status": status, "horizon_days": horizon_days,
        "targets": {"revenue": target, "cashflow": target_cf, "max_failure_rate": max_failure},
        "current": {"revenue": revenue, "cashflow": cashflow, "failure_rate": failure},
        "progress": {"revenue_percent": round(progress, 2)},
        "gaps": {"revenue": round(gap, 2), "cashflow": None if cf_gap is None else round(cf_gap, 2)},
        "required_pace": {"daily_revenue": round(max(0, gap) / horizon_days, 2),
                          "daily_cashflow": None if cf_gap is None else round(cf_gap / horizon_days, 2)},
        "failure_rate": {"status": "not_configured" if max_failure is None else (
            "on_target" if failure <= max_failure else "above_limit"),
                         "current": failure, "max_allowed": max_failure},
        "principles": ["Targets are management inputs, not historical facts.",
                       "Progress is deterministic and calculated from supplied values.",
                       "A target is not a forecast or a guarantee."]
    }
