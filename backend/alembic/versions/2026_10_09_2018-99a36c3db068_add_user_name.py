"""add user name

Revision ID: 99a36c3db068
Revises: 531dff506e48
Create Date: 2026-10-09 20:18:38.434819

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy  # noqa: F401
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99a36c3db068'
down_revision: Union[str, None] = '531dff506e48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=100), nullable=True))
    # existing accounts get the part of their email before the @ until they change it
    op.execute("UPDATE users SET name = left(split_part(email, '@', 1), 100) WHERE name IS NULL")


def downgrade() -> None:
    op.drop_column("users", "name")
