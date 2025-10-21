"""add segment tracking to personas

Revision ID: 20251015_segment_tracking
Revises: add_rag_context_details
Create Date: 2025-10-15

Adds segment_id and segment_name fields to personas table for segment-based
persona generation architecture. These fields enable tracking which demographic
segment a persona belongs to and ensure consistency between persona attributes
and segment constraints.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251015_segment_tracking'
down_revision: Union[str, Sequence[str], None] = 'add_rag_context_details'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add segment_id and segment_name columns to personas table."""
    # Add segment_id column (foreign key to segment definitions)
    op.add_column(
        'personas',
        sa.Column('segment_id', sa.String(length=100), nullable=True)
    )

    # Add segment_name column (denormalized for quick access)
    op.add_column(
        'personas',
        sa.Column('segment_name', sa.String(length=100), nullable=True)
    )

    # Create index on segment_id for efficient segment-based queries
    op.create_index(
        'ix_personas_segment_id',
        'personas',
        ['segment_id']
    )


def downgrade():
    """Remove segment tracking columns from personas table."""
    # Drop index first
    op.drop_index('ix_personas_segment_id', table_name='personas')

    # Drop columns
    op.drop_column('personas', 'segment_name')
    op.drop_column('personas', 'segment_id')
