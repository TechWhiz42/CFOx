import {MetricCard} from "./Metrics";
import SeverityBadge from "./SeverityBadge";

function Anomaly({
                     anomalyData,
                     anomalyLoading,
                     chatLoading,
                     onInvestigate,
                 }) {
    // The standalone anomaly endpoint wraps the score under `anomaly`,
    // while the unified dashboard exposes the score object directly.
    // Normalize both shapes here so the component cannot silently render zeros.
    const data = anomalyData?.anomaly ?? anomalyData;

    return (


        <section
            style={{
                background:
                    "rgba(255,255,255,0.04)",
                border:
                    "1px solid rgba(255,255,255,0.08)",
                borderRadius: "16px",
                padding: "24px",
                marginBottom: "24px",
            }}
        >
            <div
                style={{
                    display: "flex",
                    justifyContent:
                        "space-between",
                    alignItems: "center",
                    marginBottom: "20px",
                }}
            >
                <div>
                    <h2
                        style={{
                            margin: 0,
                        }}
                    >
                        Financial Anomaly
                    </h2>

                    <p
                        style={{
                            margin:
                                "6px 0 0",
                            opacity: 0.5,
                            fontSize: "13px",
                        }}
                    >
                        Deterministic risk analysis
                    </p>
                </div>

                {data && (
                    <SeverityBadge
                        severity={
                            data.severity
                        }
                    />
                )}
            </div>

            {anomalyLoading ? (
                <div
                    style={{
                        opacity: 0.5,
                    }}
                >
                    Analyzing financial anomalies...
                </div>
            ) : !data ? (
                <div
                    style={{
                        opacity: 0.5,
                    }}
                >
                    Anomaly analysis unavailable.
                </div>
            ) : (
                <>
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "repeat(auto-fit, minmax(180px, 1fr))",
                            gap: "16px",
                            marginBottom: "20px",
                        }}
                    >
                        <MetricCard
                            title="Risk Score"
                            value={`${data.score}/100`}
                            compact
                        />

                        <MetricCard
                            title="Failure Rate"
                            value={`${data.current_failure_rate}%`}
                            subtitle={`Previous: ${data.previous_failure_rate}%`}
                            compact
                        />

                        <MetricCard
                            title="Failure Rate Change"
                            value={`${
                                data.failure_rate_change >=
                                0
                                    ? "+"
                                    : ""
                            }${data.failure_rate_change} pp`}
                            compact
                        />

                        <MetricCard
                            title="Failure Multiplier"
                            value={
                                data.failure_rate_multiplier !=
                                null
                                    ? `${data.failure_rate_multiplier}×`
                                    : "N/A"
                            }
                            compact
                        />

                        <MetricCard
                            title="Revenue Impact"
                            value={`₹${Number(
                                data.revenue_change ||
                                0
                            ).toLocaleString(
                                "en-IN",
                                {
                                    maximumFractionDigits:
                                        0,
                                }
                            )}`}
                            compact
                        />
                    </div>

                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "1fr auto",
                            gap: "24px",
                            alignItems: "end",
                        }}
                    >
                        <div>
                            <h3
                                style={{
                                    margin:
                                        "0 0 10px",
                                    fontSize:
                                        "15px",
                                }}
                            >
                                Why CFOx flagged this
                            </h3>

                            {data
                                .reasons
                                ?.length >
                            0 ? (
                                <ul
                                    style={{
                                        margin: 0,
                                        paddingLeft:
                                            "20px",
                                        lineHeight:
                                            1.7,
                                        opacity:
                                            0.8,
                                    }}
                                >
                                    {data.reasons.map(
                                        (
                                            reason,
                                            index
                                        ) => (
                                            <li
                                                key={
                                                    index
                                                }
                                            >
                                                {
                                                    reason
                                                }
                                            </li>
                                        )
                                    )}
                                </ul>
                            ) : (
                                <div
                                    style={{
                                        opacity:
                                            0.5,
                                    }}
                                >
                                    No significant
                                    anomaly detected.
                                </div>
                            )}
                        </div>

                        {data.severity !==
                            "normal" && (
                                <button
                                    onClick={
                                        onInvestigate
                                    }
                                    disabled={
                                        chatLoading
                                    }
                                >
                                    {chatLoading
                                        ? "Investigating..."
                                        : "Investigate with CFOx"}
                                </button>
                            )}
                    </div>
                </>
            )}
        </section>
    );
}

export default Anomaly;