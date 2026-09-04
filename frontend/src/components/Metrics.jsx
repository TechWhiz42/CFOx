function MetricCard({
                        title,
                        value,
                        subtitle,
                        compact = false,
                    }) {
    return (
        <div
            className={
                compact
                    ? "cfox-metric cfox-metric-compact"
                    : "cfox-metric"
            }
        >
            <div className="cfox-metric-label">
                {title}
            </div>
            <div className="cfox-metric-value">
                {value}
            </div>
            {subtitle && (
                <div className="cfox-metric-subtitle">
                    {subtitle}
                </div>
            )}
        </div>
    );
}

function MiniMetric({label, value}) {
    return (
        <div className="cfox-mini-metric">
            <div className="cfox-mini-label">{label}</div>
            <div className="cfox-mini-value">{value}</div>
        </div>
    );
}

export {MetricCard, MiniMetric};
