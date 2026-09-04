from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Transaction

PAYMENT_METHODS = ("upi", "card", "netbanking")


def normalize_payment_method(
        payment_method: str | None,
) -> str | None:
    """
    Normalize and validate a payment-method filter.

    Returns:
        None:
            All payment methods.

        "upi", "card", "netbanking":
            The selected payment method.

    Raises:
        ValueError:
            If an unsupported payment method is supplied.
    """

    if not payment_method:
        return None

    payment_method = payment_method.strip().lower()

    if payment_method == "all":
        return None

    if payment_method not in PAYMENT_METHODS:
        raise ValueError(
            f"Unsupported payment method: {payment_method}"
        )

    return payment_method


def _build_metrics(total, failed, revenue) -> dict:
    total = int(total or 0)
    failed = int(failed or 0)
    revenue = float(revenue or 0)

    failure_rate = (failed / total * 100) if total else 0.0

    return {
        "total_transactions": total,
        "failed_transactions": failed,
        "failure_rate": round(failure_rate, 2),
        "revenue": round(revenue, 2),
    }


def calculate_period_metrics(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    payment_method = normalize_payment_method(payment_method)

    query = db.query(
        func.count(Transaction.id).label("total"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.status == "failed", 1),
                    else_=0,
                )
            ),
            0,
        ).label("failed"),
        func.coalesce(
            func.sum(
                case(
                    (
                        Transaction.status == "success",
                        Transaction.amount,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("revenue"),
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
    )

    if payment_method:
        query = query.filter(
            Transaction.payment_method == payment_method
        )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    row = query.one()

    return _build_metrics(
        row.total,
        row.failed,
        row.revenue,
    )


def compare_periods(
        db: Session,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    payment_method = normalize_payment_method(payment_method)

    now = datetime.utcnow()
    current_start = now - timedelta(days=15)
    previous_start = now - timedelta(days=30)

    previous = calculate_period_metrics(
        db,
        previous_start,
        current_start,
        payment_method,
        user_id,
    )

    current = calculate_period_metrics(
        db,
        current_start,
        now,
        payment_method,
        user_id,
    )

    failure_change = round(
        current["failure_rate"] - previous["failure_rate"],
        2,
    )

    multiplier = None

    if previous["failure_rate"] > 0:
        multiplier = round(
            current["failure_rate"] / previous["failure_rate"],
            2,
        )

    revenue_change = round(
        current["revenue"] - previous["revenue"],
        2,
    )

    return {
        "payment_method": payment_method or "all",
        "previous_period": previous,
        "current_period": current,
        "changes": {
            "failure_rate_change_percentage_points": failure_change,
            "failure_rate_multiplier": multiplier,
            "revenue_change": revenue_change,
        },
    }


def calculate_anomaly_score(comparison: dict) -> dict:
    current = comparison["current_period"]
    previous = comparison["previous_period"]
    changes = comparison["changes"]

    failure_change = changes[
        "failure_rate_change_percentage_points"
    ]
    multiplier = changes["failure_rate_multiplier"]
    revenue_change = changes["revenue_change"]

    score = 0
    reasons = []

    if failure_change >= 10:
        score += 50
        reasons.append(
            "Failure rate increased by at least 10 percentage points."
        )
    elif failure_change >= 5:
        score += 30
        reasons.append("Failure rate increased significantly.")
    elif failure_change >= 2:
        score += 15
        reasons.append("Failure rate increased.")

    if multiplier is not None:
        if multiplier >= 4:
            score += 30
            reasons.append(
                "Failure rate is at least 4x the previous period."
            )
        elif multiplier >= 2:
            score += 20
            reasons.append(
                "Failure rate is at least 2x the previous period."
            )

    if previous["revenue"] > 0:
        revenue_percent = (
                                  revenue_change / previous["revenue"]
                          ) * 100

        if revenue_percent <= -20:
            score += 30
            reasons.append("Revenue declined by at least 20%.")
        elif revenue_percent <= -10:
            score += 20
            reasons.append("Revenue declined by at least 10%.")
        elif revenue_change < 0:
            score += 10
            reasons.append("Revenue declined.")

    score = min(score, 100)

    if score >= 70:
        severity = "critical"
    elif score >= 40:
        severity = "warning"
    else:
        severity = "normal"

    return {
        "score": score,
        "severity": severity,
        "reasons": reasons,
        "failure_rate_change": failure_change,
        "failure_rate_multiplier": multiplier,
        "revenue_change": revenue_change,
        "current_failure_rate": current["failure_rate"],
        "previous_failure_rate": previous["failure_rate"],
    }


def compare_payment_methods(
        db: Session,
        user_id: int | None = None,
) -> dict:
    """
    Compare current vs previous-period performance for all
    supported payment methods.

    Uses one PostgreSQL aggregation query instead of running
    separate queries for every payment method and period.
    """

    now = datetime.utcnow()

    current_start = now - timedelta(days=15)
    previous_start = now - timedelta(days=30)

    methods = ["upi", "card", "netbanking"]

    query = (
        db.query(
            Transaction.payment_method.label("payment_method"),

            # Current period
            func.sum(
                case(
                    (
                        Transaction.created_at >= current_start,
                        1,
                    ),
                    else_=0,
                )
            ).label("current_transactions"),

            func.sum(
                case(
                    (
                        (Transaction.created_at >= current_start)
                        & (Transaction.status == "failed"),
                        1,
                    ),
                    else_=0,
                )
            ).label("current_failed"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.created_at >= current_start)
                            & (Transaction.status == "success"),
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("current_revenue"),

            # Previous period
            func.sum(
                case(
                    (
                        Transaction.created_at < current_start,
                        1,
                    ),
                    else_=0,
                )
            ).label("previous_transactions"),

            func.sum(
                case(
                    (
                        (Transaction.created_at < current_start)
                        & (Transaction.status == "failed"),
                        1,
                    ),
                    else_=0,
                )
            ).label("previous_failed"),

            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.created_at < current_start)
                            & (Transaction.status == "success"),
                            Transaction.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("previous_revenue"),
        )
        .filter(
            Transaction.created_at >= previous_start,
            Transaction.created_at <= now,
            Transaction.payment_method.in_(methods),
        )
    )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    rows = query.group_by(Transaction.payment_method).all()

    result = {}

    for row in rows:
        current_total = int(row.current_transactions or 0)
        current_failed = int(row.current_failed or 0)

        previous_total = int(row.previous_transactions or 0)
        previous_failed = int(row.previous_failed or 0)

        current_revenue = Decimal(
            str(row.current_revenue or 0)
        )

        previous_revenue = Decimal(
            str(row.previous_revenue or 0)
        )

        current_failure_rate = (
            (Decimal(current_failed) / Decimal(current_total))
            * Decimal("100")
            if current_total > 0
            else Decimal("0")
        )

        previous_failure_rate = (
            (Decimal(previous_failed) / Decimal(previous_total))
            * Decimal("100")
            if previous_total > 0
            else Decimal("0")
        )

        failure_rate_change = (
                current_failure_rate - previous_failure_rate
        )

        if previous_failure_rate > 0:
            failure_rate_multiplier = (
                    current_failure_rate / previous_failure_rate
            )
        else:
            failure_rate_multiplier = None

        revenue_change = (
                current_revenue - previous_revenue
        )

        result[row.payment_method] = {
            "current_period": {
                "total_transactions": current_total,
                "failed_transactions": current_failed,
                "failure_rate": float(
                    current_failure_rate.quantize(
                        Decimal("0.01")
                    )
                ),
                "revenue": float(
                    current_revenue.quantize(
                        Decimal("0.01")
                    )
                ),
            },
            "previous_period": {
                "total_transactions": previous_total,
                "failed_transactions": previous_failed,
                "failure_rate": float(
                    previous_failure_rate.quantize(
                        Decimal("0.01")
                    )
                ),
                "revenue": float(
                    previous_revenue.quantize(
                        Decimal("0.01")
                    )
                ),
            },
            "changes": {
                "failure_rate_change_percentage_points": float(
                    failure_rate_change.quantize(
                        Decimal("0.01")
                    )
                ),
                "failure_rate_multiplier": (
                    float(
                        failure_rate_multiplier.quantize(
                            Decimal("0.01")
                        )
                    )
                    if failure_rate_multiplier is not None
                    else None
                ),
                "revenue_change": float(
                    revenue_change.quantize(
                        Decimal("0.01")
                    )
                ),
            },
        }

    # Preserve the API contract even when a payment method has
    # no transactions in the selected period.
    for method in methods:
        if method not in result:
            result[method] = {
                "current_period": {
                    "total_transactions": 0,
                    "failed_transactions": 0,
                    "failure_rate": 0.0,
                    "revenue": 0.0,
                },
                "previous_period": {
                    "total_transactions": 0,
                    "failed_transactions": 0,
                    "failure_rate": 0.0,
                    "revenue": 0.0,
                },
                "changes": {
                    "failure_rate_change_percentage_points": 0.0,
                    "failure_rate_multiplier": None,
                    "revenue_change": 0.0,
                },
            }

    return result


# =========================================================
# PHASE 9 — ADVANCED FINANCIAL ANALYTICS
# =========================================================

def calculate_advanced_kpis(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """Calculate CFO-level KPIs for a time window."""
    payment_method = normalize_payment_method(payment_method)

    query = db.query(
        func.count(Transaction.id).label("total"),
        func.coalesce(
            func.sum(case((Transaction.status == "success", 1), else_=0)), 0
        ).label("successful"),
        func.coalesce(
            func.sum(case((Transaction.status == "failed", 1), else_=0)), 0
        ).label("failed"),
        func.coalesce(
            func.sum(case((Transaction.status == "refunded", 1), else_=0)), 0
        ).label("refunded"),
        func.coalesce(
            func.sum(case((Transaction.status == "success", Transaction.amount), else_=0)), 0
        ).label("gross_revenue"),
        func.coalesce(
            func.sum(case((Transaction.status == "refunded", Transaction.amount), else_=0)), 0
        ).label("refunded_amount"),
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
    )

    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    row = query.one()
    total = int(row.total or 0)
    successful = int(row.successful or 0)
    failed = int(row.failed or 0)
    refunded = int(row.refunded or 0)
    gross = Decimal(str(row.gross_revenue or 0))
    refunded_amount = Decimal(str(row.refunded_amount or 0))
    net = gross - refunded_amount

    return {
        "payment_method": payment_method or "all",
        "total_transactions": total,
        "successful_transactions": successful,
        "failed_transactions": failed,
        "refunded_transactions": refunded,
        "success_rate": round(successful / total * 100, 2) if total else 0.0,
        "failure_rate": round(failed / total * 100, 2) if total else 0.0,
        "refund_rate": round(refunded / total * 100, 2) if total else 0.0,
        "gross_revenue": float(gross.quantize(Decimal("0.01"))),
        "refunded_amount": float(refunded_amount.quantize(Decimal("0.01"))),
        "net_revenue": float(net.quantize(Decimal("0.01"))),
        "average_successful_transaction": float(
            (gross / Decimal(successful)).quantize(Decimal("0.01"))
        ) if successful else 0.0,
    }


def get_daily_performance(
        db: Session,
        days: int = 30,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> list[dict]:
    """Return one aggregate row per UTC calendar day."""
    payment_method = normalize_payment_method(payment_method)
    end_date = datetime.utcnow()
    # Return exactly `days` calendar days, including today.
    # The previous rolling 24h*days window could omit transactions
    # from today when the result list was built from midnight boundaries.
    start_day = (end_date - timedelta(days=days - 1)).date()
    start_date = datetime.combine(start_day, datetime.min.time())

    query = db.query(
        func.date(Transaction.created_at).label("day"),
        func.count(Transaction.id).label("total"),
        func.coalesce(func.sum(case((Transaction.status == "success", 1), else_=0)), 0).label("successful"),
        func.coalesce(func.sum(case((Transaction.status == "failed", 1), else_=0)), 0).label("failed"),
        func.coalesce(func.sum(case((Transaction.status == "refunded", 1), else_=0)), 0).label("refunded"),
        func.coalesce(func.sum(case((Transaction.status == "success", Transaction.amount), else_=0)), 0).label(
            "revenue"),
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
    )

    if payment_method:
        query = query.filter(Transaction.payment_method == payment_method)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    rows = query.group_by(func.date(Transaction.created_at)).order_by(func.date(Transaction.created_at)).all()
    by_day = {}
    for row in rows:
        total = int(row.total or 0)
        failed = int(row.failed or 0)
        by_day[str(row.day)] = {
            "date": str(row.day),
            "total_transactions": total,
            "successful_transactions": int(row.successful or 0),
            "failed_transactions": failed,
            "refunded_transactions": int(row.refunded or 0),
            "failure_rate": round(failed / total * 100, 2) if total else 0.0,
            "revenue": float(Decimal(str(row.revenue or 0)).quantize(Decimal("0.01"))),
        }

    result = []
    cursor = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = end_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    while cursor < end_day:
        key = cursor.date().isoformat()
        result.append(by_day.get(key, {
            "date": key,
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "refunded_transactions": 0,
            "failure_rate": 0.0,
            "revenue": 0.0,
        }))
        cursor += timedelta(days=1)
    return result


def get_customer_concentration(
        db: Session,
        days: int = 30,
        top_n: int = 10,
        payment_method: str | None = None,
        user_id: int | None = None,
) -> dict:
    """Measure revenue concentration among identifiable customers."""
    payment_method = normalize_payment_method(payment_method)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    base = db.query(
        Transaction.customer_id.label("customer_id"),
        func.coalesce(func.sum(case((Transaction.status == "success", Transaction.amount), else_=0)), 0).label(
            "revenue"),
        func.sum(case((Transaction.status == "success", 1), else_=0)).label("successful_transactions"),
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
        Transaction.customer_id.isnot(None),
        Transaction.customer_id != "",
    )
    if payment_method:
        base = base.filter(Transaction.payment_method == payment_method)
    if user_id is not None:
        base = base.filter(Transaction.user_id == user_id)

    rows = base.group_by(Transaction.customer_id).order_by(
        func.sum(case((Transaction.status == "success", Transaction.amount), else_=0)).desc()).limit(top_n).all()

    total_query = db.query(
        func.coalesce(func.sum(case((Transaction.status == "success", Transaction.amount), else_=0)), 0)
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.created_at < end_date,
    )
    if payment_method:
        total_query = total_query.filter(Transaction.payment_method == payment_method)
    if user_id is not None:
        total_query = total_query.filter(Transaction.user_id == user_id)

    total_revenue = Decimal(str(total_query.scalar() or 0))
    customers = []
    for row in rows:
        revenue = Decimal(str(row.revenue or 0))
        customers.append({
            "customer_id": row.customer_id,
            "revenue": float(revenue.quantize(Decimal("0.01"))),
            "revenue_share": round(float(revenue / total_revenue * 100), 2) if total_revenue else 0.0,
            "successful_transactions": int(row.successful_transactions or 0),
        })

    top_revenue = sum(Decimal(str(item["revenue"])) for item in customers)
    return {
        "days": days,
        "top_n": top_n,
        "payment_method": payment_method or "all",
        "total_revenue": float(total_revenue.quantize(Decimal("0.01"))),
        "top_customers_revenue": float(top_revenue.quantize(Decimal("0.01"))),
        "top_customers_revenue_share": round(float(top_revenue / total_revenue * 100), 2) if total_revenue else 0.0,
        "customers": customers,
    }
