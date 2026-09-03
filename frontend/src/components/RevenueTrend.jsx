import RevenueTimeline from "./RevenueTimeline";

function RevenueTrend({
    revenueHistoryLoading,
    historyDays,
    forecastDays,
    paymentMethod,
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
                    display: "flex",
                    justifyContent:
                        "space-between",
                    alignItems: "flex-start",
                    gap: "16px",
                    marginBottom: "20px",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <h2 style={{ margin: 0 }}>
                        Revenue Trend
                    </h2>

                    <p
                        style={{
                            margin:
                                "6px 0 0",
                            opacity: 0.5,
                            fontSize: "13px",
                        }}
                    >
                        30-day actual revenue → 7-day forecast
                        ·{" "}
                        {paymentMethod === "all"
                            ? "All payment methods"
                            : paymentMethod.toUpperCase()}
                    </p>
                </div>

                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "14px",
                        fontSize: "11px",
                        opacity: 0.65,
                    }}
                >
                    <span
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                        }}
                    >
                        <span
                            style={{
                                width: "8px",
                                height: "8px",
                                borderRadius: "50%",
                                background:
                                    "#a78bfa",
                            }}
                        />
                        Actual
                    </span>

                    <span
                        style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                        }}
                    >
                        <span
                            style={{
                                width: "8px",
                                height: "8px",
                                borderRadius: "50%",
                                background:
                                    "#34d399",
                            }}
                        />
                        Forecast
                    </span>
                </div>
            </div>

            {revenueHistoryLoading ? (
                <div
                    style={{
                        height: "280px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        opacity: 0.45,
                        fontSize: "13px",
                    }}
                >
                    Loading revenue history...
                </div>
            ) : (
                <RevenueTimeline
                    history={historyDays}
                    forecast={forecastDays}
                />
            )}
        </section>
    );
}

export default RevenueTrend;