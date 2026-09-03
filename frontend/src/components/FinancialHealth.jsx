function FinancialHealth({
                             financialHealth, financialHealthLoading,
                         }) {
    const formatScore = (value) => {
        const score = Number(value);

        if (!Number.isFinite(score)) {
            return "--";
        }

        return Math.round(score);
    };

    const getStatusLabel = (status) => {
        switch (status) {
            case "healthy":
                return "Healthy";
            case "stable":
                return "Stable";
            case "at_risk":
                return "At Risk";
            case "critical":
                return "Critical";
            default:
                return "Unknown";
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case "healthy":
                return "healthy";
            case "stable":
                return "stable";
            case "at_risk":
                return "at-risk";
            case "critical":
                return "critical";
            default:
                return "unknown";
        }
    };

    const components = financialHealth?.health?.components || {};

    const rows = [{
        key: "revenue", label: "Revenue trend", value: components.revenue, max: 30,
    }, {
        key: "payment_reliability", label: "Payment reliability", value: components.payment_reliability, max: 30,
    }, {
        key: "cashflow", label: "Cash-flow risk", value: components.cashflow, max: 25,
    }, {
        key: "anomaly", label: "Anomaly risk", value: components.anomaly, max: 15,
    },];

    return (<section className="cfox-financial-health">
            <div className="cfox-financial-health-header">
                <div>
                    <div className="cfox-section-kicker">
                        FINANCIAL HEALTH
                    </div>

                    <h2>Business health score</h2>

                    <p>
                        A deterministic view of your current financial
                        position across revenue, payments, cash flow and
                        anomalies.
                    </p>
                </div>

                {financialHealth?.payment_method && (<div className="cfox-financial-health-method">
                        {financialHealth.payment_method === "all" ? "All payment methods" : financialHealth.payment_method.toUpperCase()}
                    </div>)}
            </div>

            {financialHealthLoading ? (<div className="cfox-financial-health-loading">
                    <div className="cfox-financial-health-score-skeleton"/>
                    <div className="cfox-financial-health-lines">
                        <span/>
                        <span/>
                        <span/>
                        <span/>
                    </div>
                </div>) : !financialHealth?.health ? (<div className="cfox-financial-health-empty">
                    Financial health analysis is currently unavailable.
                </div>) : (<div className="cfox-financial-health-body">
                    <div className="cfox-financial-health-score">
                        <div
                            className="cfox-financial-health-score-ring"
                            style={{
                                background: `
            radial-gradient(
                circle at center,
                #ffffff 57%,
                transparent 58%
            ),
            conic-gradient(
                #2f66ff 0deg,
                #5b7cff ${Math.max(0, Math.min(Number(financialHealth.health.score) || 0, 100)) * 3.6}deg,
                #e8edf5 ${Math.max(0, Math.min(Number(financialHealth.health.score) || 0, 100)) * 3.6}deg,
                #e8edf5 360deg
            )
        `,
                            }}
                        >
                            <div>
                                <strong>
                                    {formatScore(financialHealth.health.score)}
                                </strong>

                                <span>/100</span>
                            </div>
                        </div>

                        <div
                            className={`cfox-financial-health-status ${getStatusClass(financialHealth.health.status)}`}
                        >
                            {getStatusLabel(financialHealth.health.status)}
                        </div>
                    </div>

                    <div className="cfox-financial-health-breakdown">
                        {rows.map((row) => {
                            const value = Number(row.value);

                            const safeValue = Number.isFinite(value) ? Math.max(0, Math.min(value, row.max)) : 0;

                            const percentage = row.max > 0 ? (safeValue / row.max) * 100 : 0;

                            return (<div
                                    className="cfox-health-row"
                                    key={row.key}
                                >
                                    <div className="cfox-health-row-top">
                                        <span>
                                            {row.label}
                                        </span>

                                        <strong>
                                            {Number.isFinite(value) ? `${value.toFixed(1)} / ${row.max}` : "--"}
                                        </strong>
                                    </div>

                                    <div className="cfox-health-track">
                                        <div
                                            className="cfox-health-fill"
                                            style={{
                                                width: `${percentage}%`,
                                            }}
                                        />
                                    </div>
                                </div>);
                        })}
                    </div>
                </div>)}
        </section>);
}

export default FinancialHealth;