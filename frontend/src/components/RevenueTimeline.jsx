import { MiniMetric } from "./Metrics";

function isValidNumber(value) {
    const number = Number(value);
    return Number.isFinite(number);
}

function normalizeActualHistory(history) {
    if (!Array.isArray(history)) {
        return [];
    }

    return history
        .filter(
            (item) =>
                item &&
                typeof item === "object" &&
                item.date &&
                isValidNumber(item.revenue)
        )
        .map((item) => ({
            date: item.date,
            value: Number(item.revenue),
        }));
}

function normalizeForecast(forecast) {
    if (!Array.isArray(forecast)) {
        return [];
    }

    return forecast
        .filter(
            (item) =>
                item &&
                typeof item === "object" &&
                item.date &&
                isValidNumber(item.predicted_revenue)
        )
        .map((item) => ({
            date: item.date,
            value: Number(item.predicted_revenue),
        }));
}

function formatDate(date) {
    if (!date) {
        return "—";
    }

    const parsed = new Date(`${date}T00:00:00`);

    if (Number.isNaN(parsed.getTime())) {
        return "—";
    }

    return parsed.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
    });
}

function formatCurrency(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "₹0";
    }

    return `₹${number.toLocaleString("en-IN", {
        maximumFractionDigits: 0,
    })}`;
}

function RevenueTimeline({
    history,
    forecast,
}) {
    const actual = normalizeActualHistory(history);
    const projected = normalizeForecast(forecast);

    /*
     * ---------------------------------------------------------
     * Empty state
     * ---------------------------------------------------------
     */

    if (actual.length === 0 && projected.length === 0) {
        return (
            <div
                style={{
                    minHeight: "280px",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    padding: "32px",
                    color: "var(--cfox-muted)",
                    textAlign: "center",
                }}
            >
                <div
                    style={{
                        width: "42px",
                        height: "42px",
                        display: "grid",
                        placeItems: "center",
                        borderRadius: "12px",
                        background: "var(--cfox-blue-soft)",
                        color: "var(--cfox-blue)",
                        fontSize: "18px",
                        fontWeight: 800,
                    }}
                >
                    ₹
                </div>

                <strong
                    style={{
                        color: "var(--cfox-text-strong)",
                        fontSize: "14px",
                    }}
                >
                    No revenue data yet
                </strong>

                <span
                    style={{
                        maxWidth: "360px",
                        fontSize: "12px",
                        lineHeight: 1.5,
                    }}
                >
                    Revenue history and forecast will appear here once
                    financial activity is available.
                </span>
            </div>
        );
    }

    /*
     * ---------------------------------------------------------
     * Combined chart points
     * ---------------------------------------------------------
     */

    const points = [
        ...actual.map((item) => ({
            date: item.date,
            value: item.value,
            type: "actual",
        })),

        ...projected.map((item) => ({
            date: item.date,
            value: item.value,
            type: "forecast",
        })),
    ];

    const values = points.map((point) => point.value);

    const maxDataValue = Math.max(...values, 0);
    const minDataValue = Math.min(...values, 0);

    /*
     * Give the chart a little breathing room when all values
     * are identical.
     */
    const dataRange = maxDataValue - minDataValue;

    const paddingValue =
        dataRange > 0
            ? dataRange * 0.08
            : Math.max(Math.abs(maxDataValue) * 0.08, 100);

    const maxValue = maxDataValue + paddingValue;
    const minValue = Math.max(0, minDataValue - paddingValue);

    const range = maxValue - minValue || 1;

    /*
     * ---------------------------------------------------------
     * SVG dimensions
     * ---------------------------------------------------------
     */

    const width = 1000;
    const height = 320;

    const left = 70;
    const right = 24;
    const top = 26;
    const bottom = 48;

    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    const x = (index) =>
        left +
        (index / Math.max(points.length - 1, 1)) *
            chartWidth;

    const y = (value) =>
        top +
        (1 - (value - minValue) / range) *
            chartHeight;

    /*
     * ---------------------------------------------------------
     * Actual points
     * ---------------------------------------------------------
     */

    const actualPoints = actual.map((item, index) => ({
        x: x(index),
        y: y(item.value),
    }));

    /*
     * ---------------------------------------------------------
     * Forecast points
     *
     * The forecast begins immediately after the final actual
     * point. This lets the chart visually connect actual
     * performance to projected performance.
     * ---------------------------------------------------------
     */

    const forecastStartIndex = Math.max(
        actual.length - 1,
        0
    );

    const forecastPoints = projected.map(
        (item, index) => {
            const pointIndex =
                actual.length > 0
                    ? forecastStartIndex + index + 1
                    : index;

            return {
                x: x(pointIndex),
                y: y(item.value),
            };
        }
    );

    /*
     * ---------------------------------------------------------
     * SVG paths
     * ---------------------------------------------------------
     */

    const linePath = (valuesList) => {
        const validPoints = valuesList.filter(
            (point) =>
                point &&
                Number.isFinite(point.x) &&
                Number.isFinite(point.y)
        );

        return validPoints
            .map(
                (point, index) =>
                    `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
            )
            .join(" ");
    };

    const actualPath = linePath(actualPoints);

    const forecastAnchor =
        actualPoints.length > 0
            ? actualPoints[actualPoints.length - 1]
            : null;

    let forecastPath = "";

    if (forecastPoints.length > 0) {
        if (forecastAnchor) {
            const forecastLine = linePath(
                forecastPoints
            );

            forecastPath = forecastLine
                ? `M ${forecastAnchor.x} ${forecastAnchor.y} ${forecastLine.replace(
                      /^M /,
                      "L "
                  )}`
                : "";
        } else {
            forecastPath = linePath(forecastPoints);
        }
    }

    /*
     * ---------------------------------------------------------
     * Axis labels
     * ---------------------------------------------------------
     */

    const labelIndexes = [
        0,
        Math.floor((points.length - 1) * 0.25),
        Math.floor((points.length - 1) * 0.5),
        Math.floor((points.length - 1) * 0.75),
        points.length - 1,
    ].filter(
        (value, index, array) =>
            value >= 0 &&
            value < points.length &&
            array.indexOf(value) === index
    );

    const gridValues = [
        maxValue,
        maxValue - range * 0.25,
        maxValue - range * 0.5,
        maxValue - range * 0.75,
        minValue,
    ];

    /*
     * ---------------------------------------------------------
     * Summary values
     * ---------------------------------------------------------
     */

    const actualRevenue = actual.reduce(
        (total, item) => total + item.value,
        0
    );

    const forecastRevenue = projected.reduce(
        (total, item) => total + item.value,
        0
    );

    const latestActual =
        actual.length > 0
            ? actual[actual.length - 1].value
            : null;

    /*
     * ---------------------------------------------------------
     * Render
     * ---------------------------------------------------------
     */

    return (
        <div>
            {/* Header / legend */}
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "16px",
                    marginBottom: "14px",
                    flexWrap: "wrap",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "18px",
                    }}
                >
                    {actual.length > 0 && (
                        <div
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "7px",
                                color: "var(--cfox-muted)",
                                fontSize: "10px",
                                fontWeight: 700,
                            }}
                        >
                            <span
                                style={{
                                    width: "18px",
                                    height: "3px",
                                    borderRadius: "999px",
                                    background:
                                        "var(--cfox-blue)",
                                }}
                            />

                            Actual
                        </div>
                    )}

                    {projected.length > 0 && (
                        <div
                            style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "7px",
                                color: "var(--cfox-muted)",
                                fontSize: "10px",
                                fontWeight: 700,
                            }}
                        >
                            <span
                                style={{
                                    width: "18px",
                                    height: "3px",
                                    borderRadius: "999px",
                                    background:
                                        "var(--cfox-green)",
                                }}
                            />

                            Forecast
                        </div>
                    )}
                </div>

                {actual.length > 0 && (
                    <span
                        style={{
                            color: "var(--cfox-muted-2)",
                            fontSize: "10px",
                            fontWeight: 650,
                        }}
                    >
                        Latest:{" "}
                        {formatCurrency(latestActual)}
                    </span>
                )}
            </div>

            <div
                style={{
                    width: "100%",
                    overflowX: "auto",
                    borderRadius: "10px",
                }}
            >
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    width="100%"
                    height="320"
                    role="img"
                    aria-label="Revenue history and forecast"
                    style={{
                        minWidth: "700px",
                        display: "block",
                        overflow: "visible",
                    }}
                >
                    {/* Grid */}
                    {gridValues.map(
                        (value, index) => {
                            const yPosition = y(value);

                            return (
                                <g key={index}>
                                    <line
                                        x1={left}
                                        x2={width - right}
                                        y1={yPosition}
                                        y2={yPosition}
                                        stroke="var(--cfox-border)"
                                        strokeOpacity="0.65"
                                        strokeWidth="1"
                                    />

                                    <text
                                        x={left - 12}
                                        y={yPosition + 4}
                                        textAnchor="end"
                                        fill="var(--cfox-muted-2)"
                                        fontSize="10"
                                    >
                                        {formatCurrency(
                                            value
                                        )}
                                    </text>
                                </g>
                            );
                        }
                    )}

                    {/* Actual line */}
                    {actualPath && (
                        <path
                            d={actualPath}
                            fill="none"
                            stroke="var(--cfox-blue)"
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    )}

                    {/* Actual points */}
                    {actualPoints.map(
                        (point, index) => (
                            <circle
                                key={`actual-${index}`}
                                cx={point.x}
                                cy={point.y}
                                r="3.5"
                                fill="var(--cfox-blue)"
                            >
                                <title>
                                    {formatDate(
                                        actual[index].date
                                    )}{" "}
                                    ·{" "}
                                    {formatCurrency(
                                        actual[index].value
                                    )}
                                </title>
                            </circle>
                        )
                    )}

                    {/* Forecast boundary */}
                    {forecastPoints.length > 0 &&
                        forecastAnchor && (
                            <line
                                x1={forecastAnchor.x}
                                x2={forecastAnchor.x}
                                y1={top}
                                y2={height - bottom}
                                stroke="var(--cfox-border-strong)"
                                strokeDasharray="4 5"
                                strokeWidth="1"
                            />
                        )}

                    {/* Forecast line */}
                    {forecastPath && (
                        <path
                            d={forecastPath}
                            fill="none"
                            stroke="var(--cfox-green)"
                            strokeWidth="3"
                            strokeDasharray="7 6"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    )}

                    {/* Forecast points */}
                    {forecastPoints.map(
                        (point, index) => (
                            <circle
                                key={`forecast-${index}`}
                                cx={point.x}
                                cy={point.y}
                                r="3.5"
                                fill="var(--cfox-green)"
                            >
                                <title>
                                    {formatDate(
                                        projected[index].date
                                    )}{" "}
                                    ·{" "}
                                    {formatCurrency(
                                        projected[index].value
                                    )}
                                </title>
                            </circle>
                        )
                    )}

                    {/* Date labels */}
                    {labelIndexes.map((index) => (
                        <text
                            key={`label-${index}`}
                            x={x(index)}
                            y={height - 14}
                            textAnchor={
                                index === 0
                                    ? "start"
                                    : index ===
                                        points.length - 1
                                      ? "end"
                                      : "middle"
                            }
                            fill="var(--cfox-muted-2)"
                            fontSize="10"
                        >
                            {formatDate(
                                points[index].date
                            )}
                        </text>
                    ))}
                </svg>
            </div>

            {/* Summary metrics */}
            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(170px, 1fr))",
                    gap: "10px",
                    marginTop: "8px",
                }}
            >
                {actual.length > 0 && (
                    <MiniMetric
                        label="30-day actual"
                        value={formatCurrency(
                            actualRevenue
                        )}
                    />
                )}

                {projected.length > 0 && (
                    <MiniMetric
                        label="7-day forecast"
                        value={formatCurrency(
                            forecastRevenue
                        )}
                    />
                )}

                <MiniMetric
                    label="Latest actual"
                    value={
                        latestActual !== null
                            ? formatCurrency(
                                  latestActual
                              )
                            : "N/A"
                    }
                />
            </div>
        </div>
    );
}

export default RevenueTimeline;