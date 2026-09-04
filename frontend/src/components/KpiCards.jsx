import {MetricCard} from "./Metrics";

function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
    });
}

function formatCurrency(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "₹0";
    }

    return `₹${number.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
    })}`;
}

function formatCurrencyChange(value) {
    const number = Number(value);

    if (!Number.isFinite(number) || number === 0) {
        return "₹0";
    }

    const sign = number > 0 ? "+" : "-";

    return `${sign}₹${Math.abs(number).toLocaleString("en-IN", {
        maximumFractionDigits: 2,
    })}`;
}

function formatPercentage(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
    });
}

function KpiCards({
                      currentPeriod = {},
                      changes = {},
                  }) {
    const totalTransactions = Number(
        currentPeriod.total_transactions
    );

    const failedTransactions = Number(
        currentPeriod.failed_transactions
    );

    const failureRate = Number(
        currentPeriod.failure_rate
    );

    const revenue = Number(
        currentPeriod.revenue
    );

    const revenueChange = Number(
        changes.revenue_change
    );

    return (
        <section>
            <MetricCard
                title="Transactions"
                value={formatNumber(totalTransactions)}
                subtitle="Current period"
            />

            <MetricCard
                title="Failed transactions"
                value={formatNumber(failedTransactions)}
                subtitle={`Failure rate: ${formatPercentage(
                    failureRate
                )}%`}
            />

            <MetricCard
                title="Revenue"
                value={formatCurrency(revenue)}
                subtitle="Current period"
            />

            <MetricCard
                title="Revenue change"
                value={formatCurrencyChange(revenueChange)}
                subtitle="vs previous period"
            />

            <MetricCard
                title="Revenue change"
                value={formatCurrencyChange(revenueChange)}
                subtitle="vs previous period"
                trend={
                    revenueChange > 0
                        ? "positive"
                        : revenueChange < 0
                            ? "negative"
                            : "neutral"
                }
            />
        </section>
    );
}

export default KpiCards;