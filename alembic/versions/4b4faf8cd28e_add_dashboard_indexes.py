"""add_dashboard_indexes

Revision ID: 4b4faf8cd28e
Revises: 4e3cccce934c
Create Date: 2025-10-27 15:24:44.820724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b4faf8cd28e'
down_revision: Union[str, Sequence[str], None] = '4e3cccce934c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add indexes for dashboard analytics."""
    # Add index on insight_evidences.insight_type for analytics queries
    op.create_index(
        'ix_insight_evidences_insight_type',
        'insight_evidences',
        ['insight_type'],
        unique=False
    )

    # Add index on focus_groups.completed_at for weekly analytics
    op.create_index(
        'ix_focus_groups_completed_at',
        'focus_groups',
        ['completed_at'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema - Remove dashboard indexes."""
    op.drop_index('ix_focus_groups_completed_at', table_name='focus_groups')
    op.drop_index('ix_insight_evidences_insight_type', table_name='insight_evidences')
