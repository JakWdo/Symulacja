"""add rag_context_details to personas

Revision ID: add_rag_context_details
Revises: f1256ec9a5f1
Create Date: 2025-10-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_rag_context_details'
down_revision: Union[str, Sequence[str], None] = 'f1256ec9a5f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add rag_context_details JSONB column to personas table."""
    op.add_column(
        'personas',
        sa.Column('rag_context_details', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    """Remove rag_context_details column from personas table."""
    op.drop_column('personas', 'rag_context_details')
