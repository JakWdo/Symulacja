"""drop_demographics_from_project

Revision ID: ds2v3jf80pj7
Revises: 93c93945d2a6
Create Date: 2025-10-22 15:30:00.000000

Removes demographics-related columns from projects table:
- target_demographics (JSON)
- chi_square_statistic (JSON)
- p_values (JSON)
- is_statistically_valid (Boolean)
- validation_date (DateTime)

These fields are no longer needed as persona generation now uses
RAG + segment-based allocation instead of hardcoded demographics.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ds2v3jf80pj7'
down_revision: Union[str, Sequence[str], None] = '93c93945d2a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove demographics columns from projects table."""
    op.drop_column('projects', 'target_demographics')
    op.drop_column('projects', 'chi_square_statistic')
    op.drop_column('projects', 'p_values')
    op.drop_column('projects', 'is_statistically_valid')
    op.drop_column('projects', 'validation_date')


def downgrade() -> None:
    """Restore demographics columns to projects table."""
    op.add_column('projects', sa.Column('target_demographics', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('projects', sa.Column('chi_square_statistic', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('projects', sa.Column('p_values', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('projects', sa.Column('is_statistically_valid', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('projects', sa.Column('validation_date', sa.DateTime(timezone=True), nullable=True))
