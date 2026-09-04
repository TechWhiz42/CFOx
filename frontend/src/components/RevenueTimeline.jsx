import {MiniMetric} from "./Metrics";

function RevenueTimeline({
                             history,
                             forecast,
                         }) {
    const actual = Array.isArray(history)
        ? history
        : [];

    const projected = Array.isArray(forecast)
        ? forecast
        : [];

    if (
        actual.length === 0 &&
        projected.length === 0
    ) {
        return (
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
                Revenue history unavailable.
            </div>
        );
    }

    const points = [
        ...actual.map((item) => ({
            date: item.date,
            value: Number(item.revenue || 0),
            type: "actual",
        })),
        ...projected.map((item) => ({
            date: item.date,
            value: Number(
                item.predicted_revenue || 0
            ),
            type: "forecast",
        })),
    ];

    const values = points.map(
        (point) => point.value
    );

    const maxValue = Math.max(
        ...values,
        1
    );

    const minValue = Math.min(
        ...values,
        0
    );

    const range =
        maxValue - minValue || 1;

    const width = 1000;
    const height = 300;
    const left = 56;
    const right = 18;
    const top = 20;
    const bottom = 42;

    const chartWidth =
        width - left - right;

    const chartHeight =
        height - top - bottom;

    const x = (index) =>
        left +
        (index /
            Math.max(
                points.length - 1,
                1
            )) *
        chartWidth;

    const y = (value) =>
        top +
        (1 -
            (value - minValue) /
            range) *
        chartHeight;

    const actualPoints = actual.map(
        (item, index) => {
            const pointIndex = index;

            return {
                x: x(pointIndex),
                y: y(
                    Number(
                        item.revenue || 0
                    )
                ),
            };
        }
    );

    const forecastStartIndex =
        actual.length - 1;

    const forecastPoints = projected.map(
        (item, index) => {
            const pointIndex =
                forecastStartIndex +
                index + 1;

            return {
                x: x(pointIndex),
                y: y(
                    Number(
                        item.predicted_revenue ||
                        0
                    )
                ),
            };
        }
    );

    const linePath = (
        valuesList
    ) =>
        valuesList
            .map(
                (point, index) =>
                    `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`
            )
            .join(" ");

    const actualPath =
        linePath(actualPoints);

    const forecastPath =
        forecastPoints.length > 0
            ? `M ${actualPoints[actualPoints.length - 1].x} ${actualPoints[actualPoints.length - 1].y} ${linePath(
                forecastPoints
            ).replace(/^M /, "L ")}`
            : "";

    const formatDate = (date) => {
        const parsed = new Date(
            `${date}T00:00:00`
        );

        return parsed.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
            }
        );
    };

    const formatCurrency = (value) =>
        `₹${Number(value).toLocaleString(
            "en-IN",
            {
                maximumFractionDigits: 0,
            }
        )}`;

    const labelIndexes = [
        0,
        Math.floor(
            (points.length - 1) *
            0.25
        ),
        Math.floor(
            (points.length - 1) *
            0.5
        ),
        Math.floor(
            (points.length - 1) *
            0.75
        ),
        points.length - 1,
    ].filter(
        (value, index, array) =>
            array.indexOf(value) ===
            index
    );

    const gridValues = [
        maxValue,
        maxValue -
        range * 0.25,
        maxValue -
        range * 0.5,
        maxValue -
        range * 0.75,
        minValue,
    ];

    return (
        <div>
            <div
                style={{
                    width: "100%",
                    overflowX: "auto",
                }}
            >
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    width="100%"
                    height="300"
                    role="img"
                    aria-label="Revenue history and forecast"
                    style={{
                        minWidth: "700px",
                        display: "block",
                    }}
                >
                    {gridValues.map(
                        (
                            value,
                            index
                        ) => {
                            const yPosition =
                                y(value);

                            return (
                                <g
                                    key={
                                        index
                                    }
                                >
                                    <line
                                        x1={left}
                                        x2={
                                            width -
                                            right
                                        }
                                        y1={
                                            yPosition
                                        }
                                        y2={
                                            yPosition
                                        }
                                        stroke="rgba(255,255,255,0.07)"
                                        strokeWidth="1"
                                    />

                                    <text
                                        x={
                                            left -
                                            10
                                        }
                                        y={
                                            yPosition +
                                            4
                                        }
                                        textAnchor="end"
                                        fill="rgba(255,255,255,0.38)"
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

                    {actual.length > 0 && (
                        <>
                            <path
                                d={actualPath}
                                fill="none"
                                stroke="#a78bfa"
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />

                            {actualPoints.map(
                                (
                                    point,
                                    index
                                ) => (
                                    <circle
                                        key={
                                            index
                                        }
                                        cx={
                                            point.x
                                        }
                                        cy={
                                            point.y
                                        }
                                        r="3.5"
                                        fill="#a78bfa"
                                    >
                                        <title>
                                            {formatDate(
                                                actual[
                                                    index
                                                    ]
                                                    .date
                                            )}{" "}
                                            ·{" "}
                                            {formatCurrency(
                                                actual[
                                                    index
                                                    ]
                                                    .revenue
                                            )}
                                        </title>
                                    </circle>
                                )
                            )}
                        </>
                    )}

                    {forecastPoints.length > 0 && (
                        <>
                            <line
                                x1={
                                    actualPoints[
                                    actualPoints.length -
                                    1
                                        ].x
                                }
                                x2={
                                    actualPoints[
                                    actualPoints.length -
                                    1
                                        ].x
                                }
                                y1={top}
                                y2={
                                    height -
                                    bottom
                                }
                                stroke="rgba(255,255,255,0.14)"
                                strokeDasharray="4 5"
                            />

                            <path
                                d={forecastPath}
                                fill="none"
                                stroke="#34d399"
                                strokeWidth="3"
                                strokeDasharray="7 6"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />

                            {forecastPoints.map(
                                (
                                    point,
                                    index
                                ) => (
                                    <circle
                                        key={
                                            index
                                        }
                                        cx={
                                            point.x
                                        }
                                        cy={
                                            point.y
                                        }
                                        r="3.5"
                                        fill="#34d399"
                                    >
                                        <title>
                                            {formatDate(
                                                projected[
                                                    index
                                                    ]
                                                    .date
                                            )}{" "}
                                            ·{" "}
                                            {formatCurrency(
                                                projected[
                                                    index
                                                    ]
                                                    .predicted_revenue
                                            )}
                                        </title>
                                    </circle>
                                )
                            )}
                        </>
                    )}

                    {labelIndexes.map(
                        (
                            index
                        ) => (
                            <text
                                key={
                                    index
                                }
                                x={x(index)}
                                y={
                                    height -
                                    12
                                }
                                textAnchor={
                                    index ===
                                    0
                                        ? "start"
                                        : index ===
                                        points.length -
                                        1
                                            ? "end"
                                            : "middle"
                                }
                                fill="rgba(255,255,255,0.42)"
                                fontSize="10"
                            >
                                {formatDate(
                                    points[
                                        index
                                        ].date
                                )}
                            </text>
                        )
                    )}
                </svg>
            </div>

            <div
                style={{
                    display: "grid",
                    gridTemplateColumns:
                        "repeat(auto-fit, minmax(170px, 1fr))",
                    gap: "10px",
                    marginTop: "4px",
                }}
            >
                <MiniMetric
                    label="30-day actual"
                    value={formatCurrency(
                        actual.reduce(
                            (
                                total,
                                item
                            ) =>
                                total +
                                Number(
                                    item.revenue ||
                                    0
                                ),
                            0
                        )
                    )}
                />

                <MiniMetric
                    label="7-day forecast"
                    value={formatCurrency(
                        projected.reduce(
                            (
                                total,
                                item
                            ) =>
                                total +
                                Number(
                                    item.predicted_revenue ||
                                    0
                                ),
                            0
                        )
                    )}
                />

                <MiniMetric
                    label="Latest actual"
                    value={
                        actual.length > 0
                            ? formatCurrency(
                                actual[
                                actual.length -
                                1
                                    ].revenue
                            )
                            : "N/A"
                    }
                />
            </div>
        </div>
    );
}

export default RevenueTimeline;
