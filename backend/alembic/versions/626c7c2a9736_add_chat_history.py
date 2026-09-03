"""add chat history

Revision ID: 626c7c2a9736
Revises: add_chat_history
Create Date: 2026-09-03 12:36:10.101091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '626c7c2a9736'
down_revision: Union[str, Sequence[str], None] = 'add_chat_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
