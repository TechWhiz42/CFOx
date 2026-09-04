import random
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Transaction

PAYMENT_METHODS = ["upi", "card", "netbanking"]


def get_failure_probability(method, days_ago):
    # Deliberate UPI anomaly during the most recent 15 days.
    if method == "upi":
        if days_ago <= 15:
            return 0.18
        return 0.05

    if method == "card":
        return 0.04

    return 0.06


def seed_transactions(count=2000):
    db = SessionLocal()

    try:
        start_date = datetime.utcnow() - timedelta(days=90)

        transactions = []

        for i in range(count):
            days_ago = random.randint(0, 89)

            created_at = (
                    datetime.utcnow()
                    - timedelta(
                days=days_ago,
                seconds=random.randint(0, 86400)
            )
            )

            payment_method = random.choice(PAYMENT_METHODS)

            failure_probability = get_failure_probability(
                payment_method,
                days_ago
            )

            random_value = random.random()

            if random_value < failure_probability:
                status = "failed"
            elif random_value < failure_probability + 0.04:
                status = "refunded"
            else:
                status = "success"

            transaction = Transaction(
                razorpay_payment_id=f"pay_demo_{i + 1:05d}",
                amount=round(random.uniform(100, 25000), 2),
                currency="INR",
                status=status,
                payment_method=payment_method,
                customer_id=f"cust_{random.randint(1, 500):04d}",
                created_at=created_at
            )

            transactions.append(transaction)

        db.add_all(transactions)
        db.commit()

        print(f"Inserted {count} transactions.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_transactions()
