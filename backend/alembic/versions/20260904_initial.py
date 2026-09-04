"""create initial CFOx schema

Revision ID: 20260904_initial
Revises:
Create Date: 2026-09-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260904_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("razorpay_payment_id", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payment_method", sa.String(), nullable=True),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_index(
        "ix_transactions_id",
        "transactions",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_razorpay_payment_id",
        "transactions",
        ["razorpay_payment_id"],
        unique=True,
    )

    op.create_index(
        "ix_transactions_user_id",
        "transactions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_created_at",
        "transactions",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_status_created_at",
        "transactions",
        ["status", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_payment_method_created_at",
        "transactions",
        ["payment_method", "created_at"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_payment_method_status_created_at",
        "transactions",
        ["payment_method", "status", "created_at"],
        unique=False,
    )

    op.create_table(
        "razorpay_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_razorpay_webhook_events_event_id",
        "razorpay_webhook_events",
        ["event_id"],
        unique=True,
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_chat_messages_conversation_id",
        "chat_messages",
        ["conversation_id"],
        unique=False,
    )

    op.create_index(
        "ix_chat_messages_conversation_created_at",
        "chat_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chat_messages_conversation_created_at",
        table_name="chat_messages",
    )
    op.drop_index(
        "ix_chat_messages_conversation_id",
        table_name="chat_messages",
    )
    op.drop_table("chat_messages")

    op.drop_index(
        "ix_conversations_user_id",
        table_name="conversations",
    )
    op.drop_table("conversations")

    op.drop_index(
        "ix_razorpay_webhook_events_event_id",
        table_name="razorpay_webhook_events",
    )
    op.drop_table("razorpay_webhook_events")

    op.drop_index(
        "ix_transactions_payment_method_status_created_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_payment_method_created_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_status_created_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_created_at",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_user_id",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_razorpay_payment_id",
        table_name="transactions",
    )
    op.drop_index(
        "ix_transactions_id",
        table_name="transactions",
    )
    op.drop_table("transactions")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )
    op.drop_table("users")
