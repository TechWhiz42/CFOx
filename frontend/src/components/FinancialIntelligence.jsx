import {MiniMetric} from "./Metrics";

function FinancialIntelligence({
                                   cashflow,
                                   cashflowRisk,
                                   cashflowScore,
                                   forecast,
                                   forecastDays,
                                   forecastTotal,
                                   recentAverage,
                               }) {
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
                    marginBottom: "20px",
                }}
            >
                <h2
                    style={{
                        margin: 0,
                    }}
                >
                    Financial Intelligence
                </h2>

                <p
                    style={{
                        margin:
                            "6px 0 0",
                        opacity: 0.5,
                        fontSize: "13px",
                    }}
                >
                    Forecast and cash-flow outlook
                </p>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(340px, 1fr))",
                    gap: "18px",
                }}
            >
                {/* FORECAST */}

                <div
                    style={{
                        background:
                            "rgba(255,255,255,0.025)",
                        border:
                            "1px solid rgba(255,255,255,0.07)",
                        borderRadius:
                            "14px",
                        padding: "20px",
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            justifyContent:
                                "space-between",
                            alignItems:
                                "flex-start",
                            marginBottom:
                                "20px",
                        }}
                    >
                        <div>
                            <div
                                style={{
                                    fontSize:
                                        "13px",
                                    opacity: 0.55,
                                }}
                            >
                                Revenue Forecast
                            </div>

                            <div
                                style={{
                                    fontSize:
                                        "30px",
                                    fontWeight:
                                        700,
                                    marginTop:
                                        "6px",
                                }}
                            >
                                ₹
                                {forecastTotal.toLocaleString(
                                    "en-IN",
                                    {
                                        maximumFractionDigits:
                                            0,
                                    }
                                )}
                            </div>

                            <div
                                style={{
                                    fontSize:
                                        "12px",
                                    opacity: 0.5,
                                    marginTop:
                                        "4px",
                                }}
                            >
                                Expected over next{" "}
                                {
                                    forecast.forecast_days ??
                                    0
                                }{" "}
                                days
                            </div>
                        </div>

                        <div
                            style={{
                                padding:
                                    "7px 10px",
                                borderRadius:
                                    "999px",
                                background:
                                    "rgba(34,197,94,0.10)",
                                color: "#4ade80",
                                fontSize:
                                    "11px",
                                fontWeight:
                                    600,
                            }}
                        >
                            FORECAST
                        </div>
                    </div>

                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns:
                                "1fr 1fr",
                            gap: "12px",
                            marginBottom:
                                "20px",
                        }}
                    >
                        <MiniMetric
                            label="Daily average"
                            value={`₹${recentAverage.toLocaleString(
                                "en-IN",
                                {
                                    maximumFractionDigits:
                                        0,
                                }
                            )}`}
                        />

                        <MiniMetric
                            label="Forecast horizon"
                            value={`${forecast.forecast_days ?? 0} days`}
                        />
                    </div>

                    <div>
                        <div
                            style={{
                                fontSize:
                                    "11px",
                                opacity: 0.45,
                                marginBottom:
                                    "10px",
                            }}
                        >
                            Daily projection
                        </div>

                        <div
                            style={{
                                display:
                                    "flex",
                                flexDirection:
                                    "column",
                                gap: "8px",
                            }}
                        >
                            {forecastDays.map(
                                (day) => {
                                    const value =
                                        Number(
                                            day.predicted_revenue ||
                                            0
                                        );

                                    const percentage =
                                        recentAverage >
                                        0
                                            ? Math.min(
                                                100,
                                                (value /
                                                    recentAverage) *
                                                100
                                            )
                                            : 0;

                                    const date =
                                        new Date(
                                            `${day.date}T00:00:00`
                                        );

                                    const formattedDate =
                                        date.toLocaleDateString(
                                            "en-IN",
                                            {
                                                day:
                                                    "2-digit",
                                                month:
                                                    "short",
                                            }
                                        );

                                    return (
                                        <div
                                            key={
                                                day.date
                                            }
                                            style={{
                                                display:
                                                    "grid",
                                                gridTemplateColumns:
                                                    "52px 1fr 95px",
                                                gap: "10px",
                                                alignItems:
                                                    "center",
                                            }}
                                        >
                                                <span
                                                    style={{
                                                        fontSize:
                                                            "11px",
                                                        opacity:
                                                            0.5,
                                                    }}
                                                >
                                                    {
                                                        formattedDate
                                                    }
                                                </span>

                                            <div
                                                style={{
                                                    height:
                                                        "6px",
                                                    borderRadius:
                                                        "999px",
                                                    background:
                                                        "rgba(255,255,255,0.07)",
                                                    overflow:
                                                        "hidden",
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        width: `${percentage}%`,
                                                        height:
                                                            "100%",
                                                        borderRadius:
                                                            "999px",
                                                        background:
                                                            "rgba(255,255,255,0.55)",
                                                    }}
                                                />
                                            </div>

                                            <span
                                                style={{
                                                    textAlign:
                                                        "right",
                                                    fontSize:
                                                        "11px",
                                                }}
                                            >
                                                    ₹
                                                {value.toLocaleString(
                                                    "en-IN",
                                                    {
                                                        maximumFractionDigits:
                                                            0,
                                                    }
                                                )}
                                                </span>
                                        </div>
                                    );
                                }
                            )}
                        </div>
                    </div>
                </div>

                {/* CASH FLOW */}

                <div
                    style={{
                        background:
                            "rgba(255,255,255,0.025)",
                        border:
                            "1px solid rgba(255,255,255,0.07)",
                        borderRadius:
                            "14px",
                        padding: "20px",
                    }}
                >
                    <div
                        style={{
                            display:
                                "flex",
                            justifyContent:
                                "space-between",
                            alignItems:
                                "flex-start",
                            marginBottom:
                                "20px",
                        }}
                    >
                        <div>
                            <div
                                style={{
                                    fontSize:
                                        "13px",
                                    opacity:
                                        0.55,
                                }}
                            >
                                Cash-Flow Risk
                            </div>

                            <div
                                style={{
                                    fontSize:
                                        "30px",
                                    fontWeight:
                                        700,
                                    marginTop:
                                        "6px",
                                    textTransform:
                                        "uppercase",
                                }}
                            >
                                {cashflowRisk}
                            </div>
                        </div>

                        <div
                            style={{
                                padding:
                                    "7px 10px",
                                borderRadius:
                                    "999px",
                                background:
                                    "rgba(239,68,68,0.12)",
                                color:
                                    "#f87171",
                                fontSize:
                                    "11px",
                                fontWeight:
                                    700,
                            }}
                        >
                            {cashflowRisk.toUpperCase()}
                        </div>
                    </div>

                    <div
                        style={{
                            marginBottom:
                                "20px",
                        }}
                    >
                        <div
                            style={{
                                display:
                                    "flex",
                                justifyContent:
                                    "space-between",
                                marginBottom:
                                    "8px",
                            }}
                        >
                                <span
                                    style={{
                                        fontSize:
                                            "12px",
                                        opacity:
                                            0.55,
                                    }}
                                >
                                    Risk score
                                </span>

                            <strong>
                                {cashflowScore}/100
                            </strong>
                        </div>

                        <div
                            style={{
                                height:
                                    "8px",
                                background:
                                    "rgba(255,255,255,0.07)",
                                borderRadius:
                                    "999px",
                                overflow:
                                    "hidden",
                            }}
                        >
                            <div
                                style={{
                                    width: `${Math.min(
                                        100,
                                        cashflowScore
                                    )}%`,
                                    height:
                                        "100%",
                                    borderRadius:
                                        "999px",
                                    background:
                                        "rgba(239,68,68,0.75)",
                                }}
                            />
                        </div>
                    </div>

                    <div
                        style={{
                            display:
                                "grid",
                            gridTemplateColumns:
                                "1fr 1fr",
                            gap: "12px",
                            marginBottom:
                                "20px",
                        }}
                    >
                        <MiniMetric
                            label="Revenue change"
                            value={`${cashflow.revenue_change_percent > 0 ? "+" : ""}${cashflow.revenue_change_percent ?? 0}%`}
                        />

                        <MiniMetric
                            label="Failure rate"
                            value={`${cashflow.current_failure_rate ?? 0}%`}
                        />

                        <MiniMetric
                            label="Current revenue"
                            value={`₹${Number(
                                cashflow.current_period_revenue ||
                                0
                            ).toLocaleString(
                                "en-IN",
                                {
                                    maximumFractionDigits:
                                        0,
                                }
                            )}`}
                        />

                        <MiniMetric
                            label="7-day expected"
                            value={`₹${Number(
                                cashflow.expected_7_day_revenue ||
                                0
                            ).toLocaleString(
                                "en-IN",
                                {
                                    maximumFractionDigits:
                                        0,
                                }
                            )}`}
                        />
                    </div>

                    <div>
                        <div
                            style={{
                                fontSize:
                                    "11px",
                                opacity:
                                    0.45,
                                marginBottom:
                                    "10px",
                            }}
                        >
                            Risk factors
                        </div>

                        {Array.isArray(
                            cashflow.reasons
                        ) &&
                        cashflow
                            .reasons
                            .length >
                        0 ? (
                            <div
                                style={{
                                    display:
                                        "flex",
                                    flexDirection:
                                        "column",
                                    gap: "8px",
                                }}
                            >
                                {cashflow.reasons.map(
                                    (
                                        reason,
                                        index
                                    ) => (
                                        <div
                                            key={
                                                index
                                            }
                                            style={{
                                                display:
                                                    "flex",
                                                gap: "9px",
                                                fontSize:
                                                    "12px",
                                                lineHeight:
                                                    1.5,
                                                opacity:
                                                    0.8,
                                            }}
                                        >
                                                <span>
                                                    •
                                                </span>

                                            <span>
                                                    {
                                                        reason
                                                    }
                                                </span>
                                        </div>
                                    )
                                )}
                            </div>
                        ) : (
                            <div
                                style={{
                                    opacity:
                                        0.5,
                                }}
                            >
                                No major risk factors detected.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}

export default FinancialIntelligence;