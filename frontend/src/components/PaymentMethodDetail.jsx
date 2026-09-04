import {MiniMetric} from "./Metrics";

function PaymentMethodDetail({
                                 method,
                                 onClose,
                                 onInvestigate,
                                 chatLoading,
                             }) {
    const current = method?.current_period || {};
    const previous = method?.previous_period || {};

    const currentRevenue = Number(current.revenue || 0);
    const previousRevenue = Number(previous.revenue || 0);
    const revenueChange = currentRevenue - previousRevenue;

    const revenueChangePercent =
        previousRevenue > 0
            ? (revenueChange / previousRevenue) * 100
            : null;

    const failureChange = Number(method.failure_rate_change || 0);
    const multiplier = method.failure_rate_multiplier;

    const failureRate = Number(current.failure_rate || 0);
    const riskLevel =
        failureRate >= 20
            ? "critical"
            : failureRate >= 10
                ? "warning"
                : "normal";

    const riskColor =
        riskLevel === "critical"
            ? "#fb7185"
            : riskLevel === "warning"
                ? "#fbbf24"
                : "#34d399";

    return (
        <div
            style={{
                marginTop: "18px",
                padding: "22px",
                borderRadius: "16px",
                border: "1px solid rgba(139,92,246,0.22)",
                background:
                    "linear-gradient(145deg, rgba(139,92,246,0.09), rgba(255,255,255,0.018))",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: "16px",
                    marginBottom: "20px",
                }}
            >
                <div>
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                            marginBottom: "6px",
                        }}
                    >
                        <h3
                            style={{
                                margin: 0,
                                fontSize: "18px",
                                textTransform: "uppercase",
                            }}
                        >
                            {method.payment_method} performance
                        </h3>

                        <span
                            style={{
                                padding: "4px 8px",
                                borderRadius: "999px",
                                fontSize: "10px",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                color: riskColor,
                                background:
                                    riskLevel === "critical"
                                        ? "rgba(251,113,133,0.1)"
                                        : riskLevel === "warning"
                                            ? "rgba(251,191,36,0.1)"
                                            : "rgba(52,211,153,0.1)",
                                border: `1px solid ${riskColor}33`,
                            }}
                        >
                            {riskLevel}
                        </span>
                    </div>

                    <p
                        style={{
                            margin: 0,
                            opacity: 0.55,
                            fontSize: "12px",
                        }}
                    >
                        Verified comparison of the current and previous
                        periods.
                    </p>
                </div>

                <button
                    type="button"
                    onClick={onClose}
                    disabled={chatLoading}
                    style={{
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.09)",
                        boxShadow: "none",
                    }}
                >
                    Close
                </button>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(160px, 1fr))",
                    gap: "12px",
                    marginBottom: "20px",
                }}
            >
                <MiniMetric
                    label="Failure rate"
                    value={`${failureRate}%`}
                />

                <MiniMetric
                    label="Change"
                    value={`${failureChange >= 0 ? "+" : ""}${failureChange} pp`}
                />

                <MiniMetric
                    label="Failure multiplier"
                    value={
                        multiplier != null
                            ? `${multiplier}×`
                            : "N/A"
                    }
                />

                <MiniMetric
                    label="Failed transactions"
                    value={current.failed_transactions ?? 0}
                />
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(220px, 1fr))",
                    gap: "14px",
                    marginBottom: "20px",
                }}
            >
                <div
                    style={{
                        padding: "16px",
                        borderRadius: "12px",
                        background: "rgba(255,255,255,0.025)",
                        border: "1px solid rgba(255,255,255,0.06)",
                    }}
                >
                    <div
                        style={{
                            fontSize: "11px",
                            opacity: 0.45,
                            marginBottom: "10px",
                        }}
                    >
                        Transactions
                    </div>

                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "12px",
                        }}
                    >
                        <div>
                            <div
                                style={{
                                    fontSize: "11px",
                                    opacity: 0.45,
                                }}
                            >
                                Previous
                            </div>
                            <strong>
                                {previous.total_transactions ?? 0}
                            </strong>
                        </div>

                        <div>
                            <div
                                style={{
                                    fontSize: "11px",
                                    opacity: 0.45,
                                }}
                            >
                                Current
                            </div>
                            <strong>
                                {current.total_transactions ?? 0}
                            </strong>
                        </div>
                    </div>
                </div>

                <div
                    style={{
                        padding: "16px",
                        borderRadius: "12px",
                        background: "rgba(255,255,255,0.025)",
                        border: "1px solid rgba(255,255,255,0.06)",
                    }}
                >
                    <div
                        style={{
                            fontSize: "11px",
                            opacity: 0.45,
                            marginBottom: "10px",
                        }}
                    >
                        Revenue
                    </div>

                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "12px",
                        }}
                    >
                        <div>
                            <div
                                style={{
                                    fontSize: "11px",
                                    opacity: 0.45,
                                }}
                            >
                                Previous
                            </div>
                            <strong>
                                ₹
                                {previousRevenue.toLocaleString("en-IN", {
                                    maximumFractionDigits: 0,
                                })}
                            </strong>
                        </div>

                        <div>
                            <div
                                style={{
                                    fontSize: "11px",
                                    opacity: 0.45,
                                }}
                            >
                                Current
                            </div>
                            <strong>
                                ₹
                                {currentRevenue.toLocaleString("en-IN", {
                                    maximumFractionDigits: 0,
                                })}
                            </strong>
                        </div>
                    </div>

                    <div
                        style={{
                            marginTop: "10px",
                            fontSize: "12px",
                            color:
                                revenueChange < 0
                                    ? "#fb7185"
                                    : "#34d399",
                        }}
                    >
                        {revenueChange >= 0 ? "+" : ""}₹
                        {revenueChange.toLocaleString("en-IN", {
                            maximumFractionDigits: 0,
                        })}
                        {revenueChangePercent != null
                            ? ` (${revenueChangePercent >= 0 ? "+" : ""}${revenueChangePercent.toFixed(2)}%)`
                            : ""}
                    </div>
                </div>
            </div>

            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "14px",
                    paddingTop: "16px",
                    borderTop: "1px solid rgba(255,255,255,0.06)",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <div
                        style={{
                            fontSize: "11px",
                            opacity: 0.45,
                            marginBottom: "4px",
                        }}
                    >
                        CFOx investigation
                    </div>

                    <div
                        style={{
                            fontSize: "12px",
                            opacity: 0.65,
                        }}
                    >
                        Ask the AI only when you want an explanation.
                    </div>
                </div>

                <button
                    type="button"
                    onClick={() => onInvestigate(method)}
                    disabled={chatLoading}
                >
                    {chatLoading
                        ? "Investigating..."
                        : "Investigate with CFOx"}
                </button>
            </div>
        </div>
    );
}

export default PaymentMethodDetail;