"""simplify_focus_groups_remove_complex_metrics

Revision ID: 9755d61029ad
Revises: c98ab2715cb5
Create Date: 2025-10-02 19:13:55.875739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9755d61029ad'
down_revision: Union[str, Sequence[str], None] = 'c98ab2715cb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Simplify focus groups - remove complex metrics, keep only essential fields."""
    # Remove complex metrics from focus_groups table
    op.drop_column('focus_groups', 'polarization_score')
    op.drop_column('focus_groups', 'polarization_clusters')
    op.drop_column('focus_groups', 'overall_consistency_score')
    op.drop_column('focus_groups', 'consistency_errors_count')
    op.drop_column('focus_groups', 'consistency_error_rate')
    op.drop_column('focus_groups', 'max_response_time_ms')

    # Simplify persona_responses - remove consistency tracking
    op.drop_column('persona_responses', 'consistency_score')
    op.drop_column('persona_responses', 'contradicts_events')
    op.drop_column('persona_responses', 'retrieved_context')
    op.drop_column('persona_responses', 'response_time_ms')
    op.drop_column('persona_responses', 'llm_provider')
    op.drop_column('persona_responses', 'llm_model')
    op.drop_column('persona_responses', 'temperature')


def downgrade() -> None:
    """Restore complex metrics."""
    # Restore focus_groups columns
    op.add_column('focus_groups', sa.Column('polarization_score', sa.Float(), nullable=True))
    op.add_column('focus_groups', sa.Column('polarization_clusters', sa.JSON(), nullable=True))
    op.add_column('focus_groups', sa.Column('overall_consistency_score', sa.Float(), nullable=True))
    op.add_column('focus_groups', sa.Column('consistency_errors_count', sa.Integer(), nullable=True))
    op.add_column('focus_groups', sa.Column('consistency_error_rate', sa.Float(), nullable=True))
    op.add_column('focus_groups', sa.Column('max_response_time_ms', sa.Integer(), nullable=True))

    # Restore persona_responses columns
    op.add_column('persona_responses', sa.Column('consistency_score', sa.Float(), nullable=True))
    op.add_column('persona_responses', sa.Column('contradicts_events', sa.JSON(), nullable=True))
    op.add_column('persona_responses', sa.Column('retrieved_context', sa.JSON(), nullable=True))
    op.add_column('persona_responses', sa.Column('response_time_ms', sa.Integer(), nullable=True))
    op.add_column('persona_responses', sa.Column('llm_provider', sa.String(50), nullable=True))
    op.add_column('persona_responses', sa.Column('llm_model', sa.String(255), nullable=True))
    op.add_column('persona_responses', sa.Column('temperature', sa.Float(), nullable=True))
