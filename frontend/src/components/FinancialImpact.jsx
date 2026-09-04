function ImpactMetric({
                          label,
                          value,
                          accent,
                      }) {
    return (
        <div
            style={{
                padding: "16px",
                borderRadius: "12px",
                background:
                    "rgba(255,255,255,0.025)",
                border:
                    "1px solid rgba(255,255,255,0.06)",
                minWidth: 0,
            }}
        >
            <div
                style={{
                    fontSize: "11px",
                    opacity: 0.5,
                    marginBottom: "8px",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                }}
            >
                {label}
            </div>

            <div
                style={{
                    fontSize: "20px",
                    fontWeight: 700,
                    color: accent || "inherit",
                    lineHeight: 1.2,
                }}
            >
                {value}
            </div>
        </div>
    );
}

function FinancialImpact({
                             dashboard,
                             alerts,
                             paymentMethod,
                             onInvestigate,
                             chatLoading,
                         }) {
    const analysis =
        dashboard?.analysis || {};

    const currentPeriod =
        analysis?.current_period || {};

    const previousPeriod =
        analysis?.previous_period || {};

    const changes =
        analysis?.changes || {};

    const cashflow =
        dashboard?.cashflow || {};

    const currentRevenue = Number(
        currentPeriod.revenue || 0
    );

    const previousRevenue = Number(
        previousPeriod.revenue || 0
    );

    const revenueChange = Number(
        changes.revenue_change_percentage ??
        changes.revenue_change_percent ??
        (previousRevenue > 0
            ? ((currentRevenue - previousRevenue) /
                previousRevenue) *
            100
            : 0)
    );

    const failureRate = Number(
        currentPeriod.failure_rate || 0
    );

    const failureRateChange = Number(
        changes.failure_rate_change_percentage_points ??
        changes.failure_rate_change ??
        0
    );

    const riskScore = Number(
        cashflow.risk_score ??
        changes.risk_score ??
        0
    );

    const hasData =
        Object.keys(analysis).length > 0 ||
        Object.keys(cashflow).length > 0;

    if (!hasData) {
        return null;
    }

    const critical =
        revenueChange <= -20 ||
        failureRate >= 20 ||
        riskScore >= 80;

    const revenueDelta =
        currentRevenue - previousRevenue;

    const formatCurrency = (value) =>
        `₹${Number(value).toLocaleString("en-IN", {
            maximumFractionDigits: 0,
        })}`;

    const methodLabel =
        paymentMethod === "all"
            ? "All payment methods"
            : paymentMethod.toUpperCase();

    return (
        <section
            style={{
                background:
                    "rgba(255,255,255,0.04)",
                border:
                    critical
                        ? "1px solid rgba(251,113,133,0.18)"
                        : "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px",
                padding: "24px",
                marginBottom: "24px",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: "16px",
                    marginBottom: "20px",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                        }}
                    >
                        <h2 style={{margin: 0}}>
                            Financial Impact
                        </h2>

                        {critical && (
                            <span
                                style={{
                                    padding: "5px 9px",
                                    borderRadius: "999px",
                                    background:
                                        "rgba(251,113,133,0.1)",
                                    color: "#fb7185",
                                    fontSize: "10px",
                                    fontWeight: 700,
                                    textTransform: "uppercase",
                                }}
                            >
                                Elevated
                            </span>
                        )}
                    </div>

                    <p
                        style={{
                            margin: "6px 0 0",
                            opacity: 0.5,
                            fontSize: "13px",
                        }}
                    >
                        Revenue performance vs payment reliability ·{" "}
                        {methodLabel}
                    </p>
                </div>

                <button
                    type="button"
                    onClick={onInvestigate}
                    disabled={chatLoading}
                >
                    {chatLoading
                        ? "Investigating..."
                        : "Investigate with CFOx"}
                </button>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(210px, 1fr))",
                    gap: "12px",
                }}
            >
                <ImpactMetric
                    label="Previous revenue"
                    value={formatCurrency(previousRevenue)}
                />

                <ImpactMetric
                    label="Current revenue"
                    value={formatCurrency(currentRevenue)}
                    accent={
                        revenueDelta < 0
                            ? "#fb7185"
                            : "#34d399"
                    }
                />

                <ImpactMetric
                    label="Revenue change"
                    value={`${revenueChange >= 0 ? "+" : ""}${revenueChange.toFixed(2)}%`}
                    accent={
                        revenueChange < 0
                            ? "#fb7185"
                            : "#34d399"
                    }
                />

                <ImpactMetric
                    label="Payment failure rate"
                    value={`${failureRate.toFixed(2)}%`}
                    accent={
                        failureRate >= 20
                            ? "#fb7185"
                            : failureRate >= 10
                                ? "#fbbf24"
                                : "#34d399"
                    }
                />
            </div>

            <div
                style={{
                    marginTop: "14px",
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(210px, 1fr))",
                    gap: "12px",
                }}
            >
                <ImpactMetric
                    label="Failure-rate change"
                    value={`${
                        failureRateChange >= 0
                            ? "+"
                            : ""
                    }${failureRateChange.toFixed(2)} pp`}
                    accent={
                        failureRateChange > 0
                            ? "#fb7185"
                            : "#34d399"
                    }
                />

                <ImpactMetric
                    label="Risk score"
                    value={`${riskScore.toFixed(0)}/100`}
                    accent={
                        riskScore >= 80
                            ? "#fb7185"
                            : riskScore >= 50
                                ? "#fbbf24"
                                : "#34d399"
                    }
                />

                <div
                    style={{
                        gridColumn:
                            "span 2",
                        padding: "16px",
                        borderRadius: "12px",
                        background:
                            critical
                                ? "rgba(251,113,133,0.055)"
                                : "rgba(255,255,255,0.025)",
                        border:
                            "1px solid rgba(255,255,255,0.06)",
                    }}
                >
                    <div
                        style={{
                            fontSize: "11px",
                            opacity: 0.45,
                            marginBottom: "7px",
                        }}
                    >
                        Financial signal
                    </div>

                    <div
                        style={{
                            fontSize: "13px",
                            lineHeight: 1.5,
                        }}
                    >
                        Revenue is{" "}
                        <strong>
                            {revenueChange < 0
                                ? "down"
                                : "up"}{" "}
                            {Math.abs(
                                revenueChange
                            ).toFixed(2)}
                            %
                        </strong>{" "}
                        while the payment failure rate is{" "}
                        <strong>
                            {failureRate.toFixed(2)}%
                        </strong>
                        {failureRateChange !== 0 && (
                            <>
                                {" "}
                                ({failureRateChange > 0
                                ? "+"
                                : ""}
                                {failureRateChange.toFixed(
                                    2
                                )} pp).
                            </>
                        )}
                    </div>

                    <div
                        style={{
                            marginTop: "7px",
                            fontSize: "11px",
                            opacity: 0.45,
                        }}
                    >
                        This is a metric relationship, not an assumed
                        root cause. Use CFOx investigation for analysis.
                    </div>
                </div>
            </div>
        </section>
    );
}

export default FinancialImpact;
