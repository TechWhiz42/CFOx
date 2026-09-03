from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction


def get_revenue_history(
    db: Session,
    days: int = 30,
    payment_method: str | None = None,
    user_id: int | None = None,
) -> dict:
    """
    Return daily successful revenue for the requested period.

    The result contains every calendar day in the requested
    range, including days with zero revenue.
    """

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = (
        db.query(
            func.date(Transaction.created_at).label("date"),
            func.sum(Transaction.amount).label("revenue"),
        )
        .filter(
            Transaction.created_at >= start_date,
            Transaction.created_at < end_date,
            Transaction.status == "success",
        )
        .group_by(
            func.date(Transaction.created_at)
        )
        .order_by(
            func.date(Transaction.created_at)
        )
    )

    if payment_method:
        query = query.filter(
            Transaction.payment_method == payment_method
        )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    rows = query.all()

    revenue_by_date = {
        str(row.date): round(
            float(row.revenue or 0),
            2,
        )
        for row in rows
    }

    history = []

    current_date = start_date.date()

    for _ in range(days):
        date_key = str(current_date)

        history.append(
            {
                "date": date_key,
                "revenue": revenue_by_date.get(
                    date_key,
                    0.0,
                ),
            }
        )

        current_date += timedelta(days=1)

    return {
        "days": days,
        "payment_method": payment_method or "all",
        "history": history,
    }