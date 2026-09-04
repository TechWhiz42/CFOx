"""add transaction user ownership

Revision ID: 9d3f2b7a1c6e
Revises: 74f8ff4335a5
Create Date: 2026-09-03 18:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9d3f2b7a1c6e"
down_revision: Union[str, Sequence[str], None] = "74f8ff4335a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_transactions_user_id",
        "transactions",
        ["user_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_transactions_user_id_users",
        "transactions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Preserve existing data when there is exactly one user.
    # When multiple users already exist, ownership is ambiguous, so
    # legacy rows remain unowned and therefore invisible to authenticated
    # analytics until explicitly assigned.
    op.execute(
        sa.text(
            """
            UPDATE transactions
            SET user_id = (SELECT id
                           FROM users
                           ORDER BY id
                LIMIT 1
                )
            WHERE user_id IS NULL
              AND (SELECT COUNT (*) FROM users) = 1
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_transactions_user_id_users",
        "transactions",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_transactions_user_id",
        table_name="transactions",
    )
    op.drop_column(
        "transactions",
        "user_id",
    )
