import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Transaction


def simulate_payment_failure_anomaly():
    db = SessionLocal()

    try:
        cutoff = datetime.utcnow() - timedelta(days=15)

        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.created_at >= cutoff,
                Transaction.payment_method == "upi",
                Transaction.status == "success"
            )
            .all()
        )

        if not transactions:
            print("No successful UPI transactions found in the last 15 days.")
            return

        sample_size = max(1, int(len(transactions) * 0.10))
        sample_size = min(sample_size, len(transactions))

        anomaly_transactions = random.sample(
            transactions,
            sample_size
        )

        for transaction in anomaly_transactions:
            transaction.status = "failed"

        db.commit()

        print(
            f"Converted {len(anomaly_transactions)} "
            f"of {len(transactions)} recent successful UPI "
            "transactions into failures."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    simulate_payment_failure_anomaly()
