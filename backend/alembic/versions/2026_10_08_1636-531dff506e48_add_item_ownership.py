"""add item ownership

Revision ID: 531dff506e48
Revises: 05ee503ffc2c
Create Date: 2026-10-08 16:36:18.640514

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy  # noqa: F401
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '531dff506e48'
down_revision: Union[str, None] = '05ee503ffc2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. add the column as nullable - existing rows have no owner yet
    op.add_column("items", sa.Column("user_id", sa.Uuid(), nullable=True))

    # 2. backfill: hand ownerless items to the earliest user; with no users at all
    #    nobody could ever reach them, so remove them
    op.execute(
        """
        UPDATE items SET user_id = (SELECT id FROM users ORDER BY created_at LIMIT 1)
        WHERE user_id IS NULL
        """
    )
    op.execute("DELETE FROM items WHERE user_id IS NULL")

    # 3. now every row has an owner, so it can be required
    op.alter_column("items", "user_id", nullable=False)

    op.create_foreign_key(
        "fk_items_user_id_users", "items", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_items_user_id", "items", ["user_id"])

    op.drop_index("uq_items_source_ref_when_url", table_name="items")
    op.create_index(
        "uq_items_user_source_ref_when_url",
        "items",
        ["user_id", "source_ref"],
        unique=True,
        postgresql_where=sa.text("source_type = 'url'"),
    )


def downgrade() -> None:
    # going back to one-url-per-app fails if two users saved the same url;
    # that's deliberate - dropping someone's data silently would be worse
    op.drop_index("uq_items_user_source_ref_when_url", table_name="items")
    op.create_index(
        "uq_items_source_ref_when_url",
        "items",
        ["source_ref"],
        unique=True,
        postgresql_where=sa.text("source_type = 'url'"),
    )
    op.drop_index("ix_items_user_id", table_name="items")
    op.drop_constraint("fk_items_user_id_users", "items", type_="foreignkey")
    op.drop_column("items", "user_id")
