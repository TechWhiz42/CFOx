"""require transaction ownership

Revision ID: b81f0f4e2a77
Revises: 9d3f2b7a1c6e
Create Date: 2026-09-03 18:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b81f0f4e2a77"
down_revision: Union[str, Sequence[str], None] = "9d3f2b7a1c6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    unowned = bind.execute(
        sa.text("SELECT COUNT(*) FROM transactions WHERE user_id IS NULL")
    ).scalar_one()

    if unowned:
        raise RuntimeError(
            f"Cannot make transactions.user_id required: {unowned} transaction(s) "
            "are still unowned. Assign them to the correct user before upgrading."
        )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
