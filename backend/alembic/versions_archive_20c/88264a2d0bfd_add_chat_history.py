"""add chat history

Revision ID: 88264a2d0bfd
Revises: 626c7c2a9736
Create Date: 2026-09-03 12:36:58.555690

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '88264a2d0bfd'
down_revision: Union[str, Sequence[str], None] = '626c7c2a9736'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
