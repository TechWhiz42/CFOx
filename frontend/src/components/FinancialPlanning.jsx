import React, {useState} from "react";
import "./FinancialPlanning.css";

export default function FinancialPlanning({authFetch, onAskCFO}) {
    const [targetRevenue, setTargetRevenue] = useState(""), [targetCashflow, setTargetCashflow] = useState("");
    const [maxFailureRate, setMaxFailureRate] = useState(""), [horizonDays, setHorizonDays] = useState(30);
    const [plan, setPlan] = useState(null), [loading, setLoading] = useState(false), [error, setError] = useState("");

    async function calculatePlan() {
        const revenue = Number(targetRevenue);
        if (!Number.isFinite(revenue) || revenue < 0) {
            setError("Enter a valid revenue target.");
            return
        }
        setLoading(true);
        setError("");
        try {
            const q = new URLSearchParams({target_revenue: String(revenue), horizon_days: String(horizonDays)});
            if (targetCashflow !== "") q.set("target_cashflow", targetCashflow);
            if (maxFailureRate !== "") q.set("max_failure_rate", maxFailureRate);
            const r = await authFetch(`/transactions/analytics/financial-plan?${q}`);
            if (!r.ok) throw new Error("Unable to calculate financial plan.");
            setPlan(await r.json());
        } catch (e) {
            setError(e.message || "Unable to calculate financial plan.")
        } finally {
            setLoading(false)
        }
    }

    const fmt = v => v == null ? "—" : Number(v).toLocaleString(undefined, {maximumFractionDigits: 2});
    return <section className="financial-planning">
        <div className="planning-header"><span>PLANNING</span><h2>Financial Targets</h2>
            <p>Set explicit management targets and measure the pace required to reach them.</p></div>
        <div className="planning-form">
            <label>Revenue target<input type="number" min="0" value={targetRevenue}
                                        onChange={e => setTargetRevenue(e.target.value)} placeholder="100000"/></label>
            <label>Cash-flow target<input type="number" value={targetCashflow}
                                          onChange={e => setTargetCashflow(e.target.value)}
                                          placeholder="50000"/></label>
            <label>Max failure %<input type="number" min="0" value={maxFailureRate}
                                       onChange={e => setMaxFailureRate(e.target.value)} placeholder="5"/></label>
            <label>Horizon (days)<input type="number" min="1" max="3650" value={horizonDays}
                                        onChange={e => setHorizonDays(Math.max(1, Math.min(3650, Number(e.target.value) || 30)))}/></label>
            <button onClick={calculatePlan} disabled={loading}>{loading ? "Calculating…" : "Calculate Plan"}</button>
        </div>
        {error && <div className="planning-error">{error}</div>}
        {plan && <div className="planning-result"><b
            className={`planning-status ${plan.status}`}>{plan.status.replace("_", " ").toUpperCase()}</b>
            <div className="planning-grid">
                <div><small>Revenue progress</small><strong>{fmt(plan.progress?.revenue_percent)}%</strong></div>
                <div><small>Revenue gap</small><strong>{fmt(plan.gaps?.revenue)}</strong></div>
                <div><small>Daily revenue required</small><strong>{fmt(plan.required_pace?.daily_revenue)}</strong>
                </div>
                <div><small>Cash-flow gap</small><strong>{fmt(plan.gaps?.cashflow)}</strong></div>
                <div><small>Failure rate</small><strong>{fmt(plan.failure_rate?.current)}%</strong></div>
                <div><small>Failure target</small><strong>{fmt(plan.failure_rate?.max_allowed)}%</strong></div>
            </div>
            <p className="planning-note">Targets are management inputs, not forecasts or guarantees.</p>
            <button className="planning-ask"
                    onClick={() => onAskCFO?.(`Explain my financial plan and the pace required to reach my target in ${plan.horizon_days} days.`)}>Ask
                CFOx
            </button>
        </div>}
    </section>
}
