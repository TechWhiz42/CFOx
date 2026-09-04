import React from "react";
import "./DecisionIntelligence.css";

function DecisionIntelligence({paymentMethod = "all", authFetch, onInvestigate}) {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        let cancelled = false;

        async function load() {
            try {
                setLoading(true);
                const query = `?payment_method=${encodeURIComponent(paymentMethod)}`;
                const response = await authFetch(
                    `http://127.0.0.1:8000/transactions/analytics/decision-intelligence${query}`
                );
                if (!response.ok) throw new Error(`Decision intelligence failed: ${response.status}`);
                const body = await response.json();
                if (!cancelled) setData(body.decision_intelligence || null);
            } catch (error) {
                if (!cancelled) {
                    console.error("Decision intelligence error:", error);
                    setData(null);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        load();
        return () => {
            cancelled = true;
        };
    }, [paymentMethod, authFetch]);

    if (loading) {
        return <section className="cfox-panel cfox-decision-panel">
            <div className="cfox-section-kicker">DECISION INTELLIGENCE</div>
            <h2>What needs attention</h2>
            <p className="cfox-muted">Evaluating verified financial signals…</p>
        </section>;
    }
    if (!data) return null;

    const signals = Array.isArray(data.signals) ? data.signals : [];
    const confidence = Math.round(Number(data.confidence || 0) * 100);
    const forecast = data.forecast || {};

    return <section className="cfox-panel cfox-decision-panel">
        <div className="cfox-decision-header">
            <div>
                <div className="cfox-section-kicker">DECISION INTELLIGENCE</div>
                <h2>What needs attention</h2>
                <p className="cfox-muted">Deterministic signals from verified financial data.</p>
            </div>
            <div className="cfox-decision-confidence">
                <strong>{confidence}%</strong><span>model confidence</span>
            </div>
        </div>

        <div className="cfox-decision-forecast">
            <div><span>Revenue outlook</span><strong>{forecast.direction || "unknown"}</strong></div>
            <div>
                <span>Recent average</span><strong>₹{Number(forecast.recent_average || 0).toLocaleString("en-IN")}</strong>
            </div>
            <div>
                <span>Forecast average</span><strong>₹{Number(forecast.projected_average || 0).toLocaleString("en-IN")}</strong>
            </div>
        </div>

        {signals.length === 0 ? <div className="cfox-decision-empty">
            <strong>No immediate decision signals.</strong>
            <span>Current verified metrics do not cross the decision thresholds.</span>
        </div> : <div className="cfox-decision-list">
            {signals.map(signal => <article className={`cfox-decision-card cfox-decision-${signal.severity}`}
                                            key={signal.id}>
                <div className="cfox-decision-card-top">
                    <div>
                        <span className="cfox-decision-badge">{signal.severity?.toUpperCase()}</span>
                        <h3>{signal.title}</h3>
                    </div>
                    <strong
                        className="cfox-decision-value">{Number(signal.value).toLocaleString("en-IN", {maximumFractionDigits: 2})}</strong>
                </div>
                <p>{signal.description}</p>
                <div className="cfox-decision-source">
                    {signal.source?.replaceAll("_", " ")} · {signal.metric?.replaceAll("_", " ")}
                </div>
                <div className="cfox-decision-action">
                    <span>{signal.recommended_action}</span>
                    {onInvestigate && signal.severity !== "positive" && (
                        <button type="button" onClick={() => onInvestigate(signal)}>Investigate</button>
                    )}
                </div>
            </article>)}
        </div>}

        <p className="cfox-decision-disclaimer">
            Forecasts are projections. Recommendations identify what to check; they do not establish an unverified
            cause.
        </p>
    </section>;
}

export default DecisionIntelligence;
