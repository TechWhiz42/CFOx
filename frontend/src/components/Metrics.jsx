function MetricCard({
    title,
    value,
    subtitle,
    compact = false,
    trend = "neutral",
    loading = false,
}) {
    const trendClass =
        trend === "positive"
            ? " cfox-metric-positive"
            : trend === "negative"
                ? " cfox-metric-negative"
                : "";

    return (
        <div
            className={
                compact
                    ? `cfox-metric cfox-metric-compact${trendClass}`
                    : `cfox-metric${trendClass}`
            }
        >
            <div className="cfox-metric-label">
                {title}
            </div>

            <div
                className="cfox-metric-value"
                aria-live="polite"
            >
                {loading ? (
                    <span
                        className="cfox-metric-skeleton"
                        aria-label="Loading"
                    />
                ) : (
                    value
                )}
            </div>

            {!loading && subtitle && (
                <div className="cfox-metric-subtitle">
                    {subtitle}
                </div>
            )}
        </div>
    );
}

function MiniMetric({ label, value }) {
    return (
        <div className="cfox-mini-metric">
            <div className="cfox-mini-label">
                {label}
            </div>

            <div className="cfox-mini-value">
                {value}
            </div>
        </div>
    );
}

export { MetricCard, MiniMetric };