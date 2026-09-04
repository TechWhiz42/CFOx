import random
from datetime import datetime, timedelta, timezone

from app.auth import hash_password
from app.database import SessionLocal
from app.models import Transaction, User

PAYMENT_METHODS = ["upi", "card", "netbanking"]
DEMO_EMAIL = "demo@cfox.local"
DEMO_PASSWORD = "StrongPassword123"


def get_failure_probability(method, days_ago):
    # Deliberate UPI anomaly during the most recent 15 days.
    if method == "upi":
        if days_ago <= 15:
            return 0.18
        return 0.05

    if method == "card":
        return 0.04

    return 0.06


def get_or_create_demo_user(db):
    user = (
        db.query(User)
        .filter(User.email == DEMO_EMAIL)
        .first()
    )

    if user is not None:
        return user

    user = User(
        email=DEMO_EMAIL,
        hashed_password=hash_password(DEMO_PASSWORD),
        is_active=1,
        created_at=datetime.now(timezone.utc),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def seed_transactions(count=2000):
    db = SessionLocal()

    try:
        user = get_or_create_demo_user(db)

        existing_count = (
            db.query(Transaction)
            .filter(Transaction.user_id == user.id)
            .count()
        )

        if existing_count:
            print(
                f"Demo user already has {existing_count} transactions. "
                "Skipping seed."
            )
            print(f"Demo email: {DEMO_EMAIL}")
            print(f"Demo password: {DEMO_PASSWORD}")
            return

        transactions = []

        for i in range(count):
            days_ago = random.randint(0, 89)

            created_at = (
                datetime.now(timezone.utc)
                - timedelta(
                    days=days_ago,
                    seconds=random.randint(0, 86400),
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
                created_at=created_at,
                user_id=user.id,
            )

            transactions.append(transaction)

        db.add_all(transactions)
        db.commit()

        print(f"Inserted {count} transactions.")
        print(f"Demo email: {DEMO_EMAIL}")
        print(f"Demo password: {DEMO_PASSWORD}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_transactions()
