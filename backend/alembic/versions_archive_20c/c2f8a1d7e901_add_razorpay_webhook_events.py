"""add razorpay webhook event idempotency table

Revision ID: c2f8a1d7e901
Revises: b81f0f4e2a77
"""

import sqlalchemy as sa
from alembic import op

revision = "c2f8a1d7e901"
down_revision = "b81f0f4e2a77"
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_index("ix_razorpay_webhook_events_event_id", table_name="razorpay_webhook_events")
    op.drop_table("razorpay_webhook_events")
