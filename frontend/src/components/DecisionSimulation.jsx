import {useEffect, useMemo, useState} from "react";
import "./DecisionSimulation.css";

const presets = [
    {name: "Conservative", revenue_change_pct: -10, failure_rate_delta_pct: 3},
    {name: "Base", revenue_change_pct: 0, failure_rate_delta_pct: 0},
    {name: "Growth", revenue_change_pct: 15, failure_rate_delta_pct: 0},
];

function money(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0
    }).format(Number(value || 0));
}

export default function DecisionSimulation({paymentMethod = "all", authFetch, onInvestigate}) {
    const [revenueChange, setRevenueChange] = useState(10);
    const [failureDelta, setFailureDelta] = useState(0);
    const [horizon, setHorizon] = useState(30);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const payload = useMemo(() => ({
        payment_method: paymentMethod || "all",
        scenarios: [
            ...presets.map((p) => ({
                name: p.name,
                revenue_change_pct: p.revenue_change_pct,
                failure_rate_delta_pct: p.failure_rate_delta_pct,
                horizon_days: horizon
            })),
            {
                name: "Custom",
                revenue_change_pct: revenueChange,
                failure_rate_delta_pct: failureDelta,
                horizon_days: horizon
            },
        ],
    }), [paymentMethod, revenueChange, failureDelta, horizon]);

    const run = async () => {
        setLoading(true);
        setError("");
        try {
            const response = await authFetch("/transactions/analytics/decision-simulation", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload),
            });
            const json = await response.json();
            if (!response.ok) throw new Error(json?.detail || json?.message || "Simulation failed");
            setData(json);
        } catch (err) {
            setError(err.message || "Simulation failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        run();
    }, [paymentMethod]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <section className="decision-simulation">
            <div className="decision-simulation__header">
                <div>
                    <span className="decision-simulation__eyebrow">DECISION INTELLIGENCE</span>
                    <h2>Decision Simulator</h2>
                    <p>Compare hypothetical business outcomes and rank the risk/upside trade-off.</p>
                </div>
                <button onClick={run} disabled={loading}>{loading ? "Simulating…" : "Run simulation"}</button>
            </div>

            <div className="decision-simulation__controls">
                <label>Revenue change <strong>{revenueChange}%</strong><input type="range" min="-30" max="30"
                                                                              value={revenueChange}
                                                                              onChange={(e) => setRevenueChange(Number(e.target.value))}/></label>
                <label>Failure-rate change <strong>{failureDelta > 0 ? "+" : ""}{failureDelta} pts</strong><input
                    type="range" min="-10" max="15" value={failureDelta}
                    onChange={(e) => setFailureDelta(Number(e.target.value))}/></label>
                <label>Horizon <strong>{horizon} days</strong><input type="range" min="7" max="90" value={horizon}
                                                                     onChange={(e) => setHorizon(Number(e.target.value))}/></label>
            </div>

            {error && <div className="decision-simulation__error">{error}</div>}
            {data?.scenarios && (
                <>
                    <div className="decision-simulation__recommendation">
                        <div><span>RECOMMENDED</span><h3>{data.recommended_scenario}</h3></div>
                        <p>Highest modeled decision score. This is a hypothetical recommendation, not a guaranteed
                            outcome.</p>
                    </div>
                    <div className="decision-simulation__grid">
                        {data.scenarios.map((item) => (
                            <article key={item.scenario.name} className={item.rank === 1 ? "is-best" : ""}>
                                <div className="decision-simulation__rank">#{item.rank}</div>
                                <h3>{item.scenario.name}</h3>
                                <div className="decision-simulation__score">{item.decision_score}<small>/100</small>
                                </div>
                                <div className="decision-simulation__risk">{item.risk_level}</div>
                                <dl>
                                    <div>
                                        <dt>Revenue</dt>
                                        <dd>{money(item.projected.revenue)}</dd>
                                    </div>
                                    <div>
                                        <dt>Revenue Δ</dt>
                                        <dd>{money(item.delta.revenue)}</dd>
                                    </div>
                                    <div>
                                        <dt>Failure rate</dt>
                                        <dd>{item.projected.failure_rate_pct}%</dd>
                                    </div>
                                    <div>
                                        <dt>Confidence</dt>
                                        <dd>{Math.round(item.confidence * 100)}%</dd>
                                    </div>
                                </dl>
                                <button onClick={() => onInvestigate?.({
                                    description: `Explain why the ${item.scenario.name} scenario ranks where it does.`,
                                    scenario: item
                                })}>Ask CFOx
                                </button>
                            </article>
                        ))}
                    </div>
                </>
            )}
        </section>
    );
}
