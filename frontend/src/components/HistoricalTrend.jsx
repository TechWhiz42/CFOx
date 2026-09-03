function HistoricalTrend({
    revenueHistory,
}) {
    const points = Array.isArray(
        revenueHistory?.history
    )
        ? revenueHistory.history
        : Array.isArray(
              revenueHistory?.data
          )
          ? revenueHistory.data
          : Array.isArray(
                revenueHistory
            )
            ? revenueHistory
            : [];

    if (points.length < 2) {
        return null;
    }

    const getRevenue = (item) =>
        Number(
            item?.revenue ??
                item?.total_revenue ??
                item?.daily_revenue ??
                0
        );

    const values = points.map(getRevenue);

    const latest = values[values.length - 1];
    const previous = values[values.length - 2];

    const firstHalf = values.slice(
        0,
        Math.max(1, Math.floor(values.length / 2))
    );

    const secondHalf = values.slice(
        Math.floor(values.length / 2)
    );

    const average = (arr) =>
        arr.length
            ? arr.reduce(
                  (sum, value) =>
                      sum + value,
                  0
              ) / arr.length
            : 0;

    const earlierAverage =
        average(firstHalf);

    const recentAverage =
        average(secondHalf);

    const recentChange =
        earlierAverage !== 0
            ? ((recentAverage -
                  earlierAverage) /
                  earlierAverage) *
              100
            : 0;

    const latestChange =
        previous !== 0
            ? ((latest - previous) /
                  previous) *
              100
            : 0;

    const direction =
        recentChange < -1
            ? "deteriorating"
            : recentChange > 1
              ? "improving"
              : "stable";

    const directionLabel =
        direction === "deteriorating"
            ? "Deteriorating"
            : direction === "improving"
              ? "Improving"
              : "Stable";

    const directionColor =
        direction === "deteriorating"
            ? "#fb7185"
            : direction === "improving"
              ? "#34d399"
              : "#fbbf24";

    const formatCurrency = (value) =>
        `₹${Number(value).toLocaleString(
            "en-IN",
            {
                maximumFractionDigits: 0,
            }
        )}`;

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
                    marginBottom: "18px",
                    flexWrap: "wrap",
                }}
            >
                <div>
                    <h2 style={{ margin: 0 }}>
                        Historical Trend
                    </h2>

                    <p
                        style={{
                            margin:
                                "6px 0 0",
                            opacity: 0.5,
                            fontSize:
                                "13px",
                        }}
                    >
                        Is revenue improving or deteriorating?
                    </p>
                </div>

                <span
                    style={{
                        padding:
                            "7px 10px",
                        borderRadius:
                            "999px",
                        background:
                            `${directionColor}18`,
                        color:
                            directionColor,
                        fontSize:
                            "10px",
                        fontWeight:
                            800,
                        textTransform:
                            "uppercase",
                    }}
                >
                    {directionLabel}
                </span>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(190px, 1fr))",
                    gap: "12px",
                }}
            >
                <TrendMetric
                    label="Recent average"
                    value={formatCurrency(
                        recentAverage
                    )}
                />

                <TrendMetric
                    label="Earlier average"
                    value={formatCurrency(
                        earlierAverage
                    )}
                />

                <TrendMetric
                    label="Trend change"
                    value={`${
                        recentChange >= 0
                            ? "+"
                            : ""
                    }${recentChange.toFixed(
                        2
                    )}%`}
                    accent={
                        recentChange < 0
                            ? "#fb7185"
                            : recentChange > 0
                              ? "#34d399"
                              : "#fbbf24"
                    }
                />

                <TrendMetric
                    label="Latest vs previous day"
                    value={`${
                        latestChange >= 0
                            ? "+"
                            : ""
                    }${latestChange.toFixed(
                        2
                    )}%`}
                    accent={
                        latestChange < 0
                            ? "#fb7185"
                            : latestChange > 0
                              ? "#34d399"
                              : "#fbbf24"
                    }
                />
            </div>

            <div
                style={{
                    marginTop:
                        "14px",
                    padding:
                        "14px 16px",
                    borderRadius:
                        "12px",
                    background:
                        "rgba(255,255,255,0.025)",
                    border:
                        "1px solid rgba(255,255,255,0.06)",
                    fontSize:
                        "12px",
                    lineHeight:
                        1.5,
                    opacity:
                        0.72,
                }}
            >
                Revenue averaged{" "}
                <strong>
                    {formatCurrency(
                        recentAverage
                    )}
                </strong>{" "}
                in the more recent half of the available
                history versus{" "}
                <strong>
                    {formatCurrency(
                        earlierAverage
                    )}
                </strong>{" "}
                in the earlier half.
            </div>
        </section>
    );
}


function TrendMetric({
    label,
    value,
    accent,
}) {
    return (
        <div
            style={{
                padding:
                    "16px",
                borderRadius:
                    "12px",
                background:
                    "rgba(255,255,255,0.025)",
                border:
                    "1px solid rgba(255,255,255,0.06)",
            }}
        >
            <div
                style={{
                    fontSize:
                        "10px",
                    opacity:
                        0.45,
                    marginBottom:
                        "7px",
                }}
            >
                {label}
            </div>

            <div
                style={{
                    fontSize:
                        "20px",
                    fontWeight:
                        700,
                    color:
                        accent ||
                        "#ffffff",
                }}
            >
                {value}
            </div>
        </div>
    );
}

export default HistoricalTrend;