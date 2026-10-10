"""require user name

Revision ID: 6b55b08a903f
Revises: 99a36c3db068
Create Date: 2026-10-10 19:46:43.103929

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy  # noqa: F401
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b55b08a903f'
down_revision: Union[str, None] = '99a36c3db068'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # the api has required a name since the previous release, so this should touch nothing -
    # it just guarantees the NOT NULL below can't fail on a leftover row
    op.execute("UPDATE users SET name = left(split_part(email, '@', 1), 100) WHERE name IS NULL")
    op.alter_column('users', 'name',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)


def downgrade() -> None:
    op.alter_column('users', 'name',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
