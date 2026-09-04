import {useEffect, useMemo, useState} from "react";
import "./ScenarioLab.css";

function money(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2
    }).format(Number(value) || 0);
}

export default function ScenarioLab({paymentMethod, authFetch, onInvestigate}) {
    const [revenueChange, setRevenueChange] = useState(0);
    const [failureChange, setFailureChange] = useState(0);
    const [horizon, setHorizon] = useState(30);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const payload = useMemo(() => ({
        payment_method: paymentMethod || "all",
        revenue_change_pct: Number(revenueChange),
        failure_rate_change_pct: Number(failureChange),
        horizon_days: Number(horizon),
    }), [paymentMethod, revenueChange, failureChange, horizon]);

    useEffect(() => {
        let cancelled = false;

        async function run() {
            setLoading(true);
            setError("");
            try {
                const response = await authFetch("/transactions/analytics/scenario", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload),
                });
                if (!response.ok) throw new Error("Scenario calculation failed");
                const json = await response.json();
                if (!cancelled) setData(json);
            } catch (e) {
                if (!cancelled) setError(e.message || "Unable to calculate scenario");
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        run();
        return () => {
            cancelled = true;
        };
    }, [authFetch, payload]);

    const projected = data?.projected || {};
    const delta = data?.delta || {};
    const risk = data?.risk || {};

    return (
        <section className="scenario-lab">
            <div className="scenario-lab__header">
                <div>
                    <div className="scenario-lab__eyebrow">DECISION INTELLIGENCE</div>
                    <h2>Scenario Lab</h2>
                    <p>Test a business assumption without changing your verified financial data.</p>
                </div>
                <span className="scenario-badge">SCENARIO</span>
            </div>

            <div className="scenario-controls">
                <label>Revenue change <strong>{revenueChange > 0 ? "+" : ""}{revenueChange}%</strong>
                    <input type="range" min="-30" max="30" step="1" value={revenueChange}
                           onChange={e => setRevenueChange(e.target.value)}/>
                </label>
                <label>Failure-rate adjustment <strong>{failureChange > 0 ? "+" : ""}{failureChange} pp</strong>
                    <input type="range" min="-10" max="15" step="1" value={failureChange}
                           onChange={e => setFailureChange(e.target.value)}/>
                </label>
                <label>Horizon <strong>{horizon} days</strong>
                    <input type="range" min="7" max="90" step="1" value={horizon}
                           onChange={e => setHorizon(e.target.value)}/>
                </label>
            </div>

            {error && <div className="scenario-error">{error}</div>}
            {loading && <div className="scenario-loading">Recalculating scenario…</div>}

            {data && !loading && (
                <>
                    <div className="scenario-metrics">
                        <div>
                            <span>Projected revenue</span><strong>{money(projected.revenue)}</strong><small>{delta.revenue >= 0 ? "+" : ""}{money(delta.revenue)}</small>
                        </div>
                        <div>
                            <span>Projected failure rate</span><strong>{Number(projected.failure_rate || 0).toFixed(2)}%</strong><small>{delta.failure_rate >= 0 ? "+" : ""}{Number(delta.failure_rate || 0).toFixed(2)} pp</small>
                        </div>
                        <div>
                            <span>Projected cash flow</span><strong>{money(projected.cashflow)}</strong><small>{delta.cashflow >= 0 ? "+" : ""}{money(delta.cashflow)}</small>
                        </div>
                        <div>
                            <span>Risk impact</span><strong>{Number(risk.score || 0).toFixed(0)}/100</strong><small>{risk.level || "low"}</small>
                        </div>
                    </div>
                    <div className="scenario-footer">
                        <span>Verified baseline → Assumption → Projected result → Delta → Risk</span>
                        <button onClick={() => onInvestigate?.({
                            title: "Scenario analysis",
                            description: "Analyze this scenario and explain the business implications.",
                            scenario: data
                        })}>
                            Ask CFOx about this scenario
                        </button>
                    </div>
                </>
            )}
        </section>
    );
}
