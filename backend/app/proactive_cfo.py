def build_proactive_alerts(*, financial_health=None, financial_actions=None, decision_simulation=None,
                           financial_plan=None):
    alerts = []
    h = (financial_health or {}).get("health") or {}
    try:
        score = float(h.get("score"))
    except (TypeError, ValueError):
        score = None
    status = str(h.get("status") or "").lower()
    if score is not None:
        if score < 40 or status == "critical":
            alerts.append(
                {"severity": "critical", "category": "financial_health", "title": "Financial health is critical",
                 "message": f"Health score is {score:.0f}/100.",
                 "recommended_action": "Review cash-flow, payment reliability, and anomalies immediately.",
                 "source": "verified_financial_health"})
        elif score < 60 or status == "at_risk":
            alerts.append(
                {"severity": "warning", "category": "financial_health", "title": "Financial health needs attention",
                 "message": f"Health score is {score:.0f}/100.",
                 "recommended_action": "Review the highest-impact financial risk signals.",
                 "source": "verified_financial_health"})
    actions = financial_actions or {}
    for x in (actions.get("actions") or actions.get("financial_actions") or [])[:8]:
        if isinstance(x, dict) and str(x.get("severity") or "").lower() in {"critical", "warning"}:
            alerts.append(
                {"severity": str(x.get("severity")).lower(), "category": x.get("category", "financial_action"),
                 "title": x.get("title", "Financial risk detected"),
                 "message": x.get("message") or x.get("description") or "",
                 "recommended_action": x.get("recommended_action") or x.get("action") or "",
                 "source": "verified_financial_action"})
    if str((financial_plan or {}).get("status") or "").lower() == "at_risk":
        alerts.append({"severity": "warning", "category": "financial_plan", "title": "Financial target is at risk",
                       "message": "Current performance is below at least one configured management target.",
                       "recommended_action": "Review the target gap and required daily pace.",
                       "source": "management_target"})
    for x in ((decision_simulation or {}).get("signals") or [])[:8]:
        if isinstance(x, dict) and str(x.get("severity") or "").lower() in {"critical", "warning"}:
            alerts.append({"severity": str(x.get("severity")).lower(), "category": "decision_simulation",
                           "title": x.get("title", "Scenario risk"),
                           "message": x.get("message") or x.get("description") or "",
                           "recommended_action": x.get("recommended_action") or "", "source": "scenario_simulation"})
    rank = {"critical": 0, "warning": 1};
    alerts.sort(key=lambda x: (rank.get(x["severity"], 9), x["category"]))
    out = [];
    seen = set()
    for x in alerts:
        if x["category"] not in seen: seen.add(x["category"]);out.append(x)
    return {"alerts": out, "count": len(out), "has_critical": any(x["severity"] == "critical" for x in out),
            "principles": ["Alerts are signals for review, not proof of a future event.",
                           "No notification is a guarantee that risk is absent."]}
