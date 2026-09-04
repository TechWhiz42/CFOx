"""add data integrity constraints

Revision ID: 20260904_constraints
Revises: 20260904_initial
Create Date: 2026-09-04

"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260904_constraints"
down_revision: Union[str, Sequence[str], None] = "20260904_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_transactions_amount_positive",
        "transactions",
        "amount > 0",
    )

    op.create_check_constraint(
        "ck_transactions_currency_inr",
        "transactions",
        "currency = 'INR'",
    )

    op.create_check_constraint(
        "ck_transactions_status_allowed",
        "transactions",
        "status IN ('success', 'failed', 'refunded')",
    )

    op.create_check_constraint(
        "ck_transactions_payment_method_allowed",
        "transactions",
        "payment_method IS NULL OR payment_method IN ('upi', 'card', 'netbanking')",
    )

    op.create_check_constraint(
        "ck_chat_messages_role_allowed",
        "chat_messages",
        "role IN ('user', 'assistant', 'system')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_chat_messages_role_allowed",
        "chat_messages",
        type_="check",
    )

    op.drop_constraint(
        "ck_transactions_payment_method_allowed",
        "transactions",
        type_="check",
    )

    op.drop_constraint(
        "ck_transactions_status_allowed",
        "transactions",
        type_="check",
    )

    op.drop_constraint(
        "ck_transactions_currency_inr",
        "transactions",
        type_="check",
    )

    op.drop_constraint(
        "ck_transactions_amount_positive",
        "transactions",
        type_="check",
    )