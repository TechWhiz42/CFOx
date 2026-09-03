import { MetricCard } from "./Metrics";

function KpiCards({
    currentPeriod,
    changes,
}) {
    return (
        <section>
            <MetricCard
                title="Transactions"
                value={
                    currentPeriod
                        .total_transactions ?? 0
                }
                subtitle="Current period"
            />

            <MetricCard
                title="Failed transactions"
                value={
                    currentPeriod
                        .failed_transactions ?? 0
                }
                subtitle={`Failure rate: ${
                    currentPeriod.failure_rate ?? 0
                }%`}
            />

            <MetricCard
                title="Revenue"
                value={`₹${Number(
                    currentPeriod.revenue || 0
                ).toLocaleString("en-IN", {
                    maximumFractionDigits: 2,
                })}`}
                subtitle="Current period"
            />

            <MetricCard
                title="Revenue change"
                value={`₹${Number(
                    changes.revenue_change || 0
                ).toLocaleString("en-IN", {
                    maximumFractionDigits: 2,
                })}`}
                subtitle="vs previous period"
            />
        </section>
    );
}

export default KpiCards;
