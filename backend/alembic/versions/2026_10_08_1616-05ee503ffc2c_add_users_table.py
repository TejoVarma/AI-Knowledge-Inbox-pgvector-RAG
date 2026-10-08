"""add users table

Revision ID: 05ee503ffc2c
Revises: e86def7545ac
Create Date: 2026-10-08 16:16:19.444739

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy  # noqa: F401
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05ee503ffc2c'
down_revision: Union[str, None] = 'e86def7545ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )


def downgrade() -> None:
    op.drop_table('users')
