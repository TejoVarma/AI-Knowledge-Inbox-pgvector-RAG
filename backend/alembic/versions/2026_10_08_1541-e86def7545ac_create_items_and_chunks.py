"""create items and chunks

Revision ID: e86def7545ac
Revises: 
Create Date: 2026-10-08 15:41:20.860171

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e86def7545ac'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('items',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('source_type', sa.Enum('note', 'url', name='sourcetype'), nullable=False),
    sa.Column('source_ref', sa.String(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('suggested_question', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_items_source_ref_when_url', 'items', ['source_ref'], unique=True, postgresql_where=sa.text("source_type = 'url'"))
    op.create_table('chunks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('item_id', sa.Uuid(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chunks_embedding_hnsw', 'chunks', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})


def downgrade() -> None:
    op.drop_index('ix_chunks_embedding_hnsw', table_name='chunks', postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.drop_table('chunks')
    op.drop_index('uq_items_source_ref_when_url', table_name='items', postgresql_where=sa.text("source_type = 'url'"))
    op.drop_table('items')
    sa.Enum(name="sourcetype").drop(op.get_bind(), checkfirst=True)
