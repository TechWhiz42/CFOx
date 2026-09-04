def build_cfo_recommendations(*, financial_health=None, financial_actions=None, decision_simulation=None):
    recs = []
    health = financial_health or {}
    h = health.get("health") or {}
    has_health_assessment = bool(h) and ("score" in h or "status" in h)
    try:
        score = float(h.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    status = str(h.get("status") or "").lower()

    if has_health_assessment and (score < 40 or status == "critical"):
        recs.append({"priority": "P0", "category": "financial_health", "title": "Stabilize financial risk",
                     "recommendation": "Prioritize cash-flow protection and payment reliability before aggressive growth.",
                     "basis": "Verified financial-health assessment"})
    elif has_health_assessment and (score < 60 or status == "at_risk"):
        recs.append({"priority": "P1", "category": "financial_health", "title": "Reduce financial pressure",
                     "recommendation": "Address the highest-impact risk signals before increasing operating commitments.",
                     "basis": "Verified financial-health assessment"})

    actions = financial_actions or {}
    for item in (actions.get("actions") or actions.get("financial_actions") or [])[:5]:
        if not isinstance(item, dict): continue
        sev = str(item.get("severity") or item.get("priority") or "warning").lower()
        pri = "P0" if sev == "critical" else "P1" if sev == "warning" else "P2"
        recs.append({"priority": pri, "category": item.get("category", "financial_action"),
                     "title": item.get("title", "Address financial signal"),
                     "recommendation": item.get("recommended_action") or item.get("recommendation") or item.get(
                         "action") or item.get("description", ""),
                     "basis": "Verified financial signal"})

    sim = decision_simulation or {}
    chosen = sim.get("recommended_scenario")
    ranked = sim.get("ranked_scenarios") or sim.get("scenarios") or []
    if isinstance(chosen, dict):
        recs.append({"priority": "P1", "category": "decision_simulation",
                     "title": f'Prefer {chosen.get("name", "the top-ranked scenario")}',
                     "recommendation": "Use the highest-ranked scenario as the current planning candidate, subject to management review.",
                     "basis": "Scenario simulation"})
    elif ranked and isinstance(ranked[0], dict):
        recs.append({"priority": "P1", "category": "decision_simulation",
                     "title": f'Review {ranked[0].get("name", "the top-ranked scenario")}',
                     "recommendation": "Review the top-ranked scenario before making an operating decision.",
                     "basis": "Scenario simulation"})

    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    recs.sort(key=lambda x: (order.get(x["priority"], 9), x["category"]))
    out = [];
    seen = set()
    for r in recs:
        if r["category"] not in seen:
            seen.add(r["category"]);
            out.append(r)
    return {
        "status": "urgent_action" if out and out[0]["priority"] == "P0" else "action_required" if out else "stable",
        "recommendations": out,
        "principles": [
            "Recommendations are derived from verified analytics or explicit scenario simulations.",
            "Forecasts and scenarios are not historical facts.",
            "Management should validate assumptions before acting."
        ]
    }
