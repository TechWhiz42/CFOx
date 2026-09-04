from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    is_active = Column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    razorpay_payment_id = Column(
        String,
        unique=True,
        index=True,
    )

    amount = Column(
        Numeric(18, 2),
        nullable=False,
    )

    currency = Column(
        String,
        nullable=True,
        default="INR",
    )

    status = Column(
        String,
        nullable=False,
    )

    payment_method = Column(
        String,
        nullable=True,
    )

    customer_id = Column(
        String,
        nullable=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive",
        ),
        CheckConstraint(
            "currency = 'INR'",
            name="ck_transactions_currency_inr",
        ),
        CheckConstraint(
            "status IN ('success', 'failed', 'refunded')",
            name="ck_transactions_status_allowed",
        ),
        CheckConstraint(
            "payment_method IS NULL OR payment_method IN ('upi', 'card', 'netbanking')",
            name="ck_transactions_payment_method_allowed",
        ),
        Index("ix_transactions_created_at", "created_at"),
        Index("ix_transactions_status_created_at", "status", "created_at"),
        Index("ix_transactions_payment_method_created_at", "payment_method", "created_at"),
        Index(
            "ix_transactions_payment_method_status_created_at",
            "payment_method",
            "status",
            "created_at",
        ),
    )


class RazorpayWebhookEvent(Base):
    __tablename__ = "razorpay_webhook_events"

    id = Column(Integer, primary_key=True)

    event_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    event_name = Column(
        String(100),
        nullable=False,
    )

    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="ck_chat_messages_role_allowed",
        ),
        Index(
            "ix_chat_messages_conversation_created_at",
            "conversation_id",
            "created_at",
        ),
    )