"""add persistent chat history

Revision ID: add_chat_history
Revises: c2f8a1d7e901
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa


revision = "add_chat_history"
down_revision = "c2f8a1d7e901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_conversations_user_id",
        "conversations",
        ["user_id"],
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey(
                "conversations.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_chat_messages_conversation_id",
        "chat_messages",
        ["conversation_id"],
    )

    op.create_index(
        "ix_chat_messages_conversation_created_at",
        "chat_messages",
        ["conversation_id", "created_at"],
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