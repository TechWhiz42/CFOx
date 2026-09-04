"""make timestamps timezone aware

Revision ID: 20260904_timestamps_tz
Revises: 20260904_constraints
Create Date: 2026-09-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260904_timestamps_tz"
down_revision: Union[str, Sequence[str], None] = "20260904_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table_name, column_name, nullable in (
        ("users", "created_at", False),
        ("transactions", "created_at", True),
        ("razorpay_webhook_events", "received_at", False),
        ("conversations", "created_at", False),
        ("conversations", "updated_at", False),
        ("chat_messages", "created_at", False),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=nullable,
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table_name, column_name, nullable in (
        ("users", "created_at", False),
        ("transactions", "created_at", True),
        ("razorpay_webhook_events", "received_at", False),
        ("conversations", "created_at", False),
        ("conversations", "updated_at", False),
        ("chat_messages", "created_at", False),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=nullable,
            postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
        )