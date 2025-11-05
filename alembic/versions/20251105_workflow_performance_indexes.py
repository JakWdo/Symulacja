"""workflow performance indexes

Revision ID: 20251105_perf_idx
Revises: 45c8ede416fb
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_perf_idx'
down_revision = '45c8ede416fb'
branch_labels = None
depends_on = None


def upgrade():
    """
    Dodaje indeksy wydajnościowe dla tabel workflows i workflow_executions.

    Indeksy zoptymalizowane dla:
    - Filtrowanie workflows per projekt + status
    - Lista workflows użytkownika sorted by created_at DESC
    - Execution history per workflow + status filter
    - Znajdowanie wszystkich running/pending executions (monitoring)
    - Execution history posortowana chronologicznie
    """

    # Performance indexes dla workflows table
    op.create_index(
        'idx_workflows_project_status',
        'workflows',
        ['project_id', 'status'],
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    op.create_index(
        'idx_workflows_owner_created',
        'workflows',
        ['owner_id', 'created_at'],
        postgresql_using='btree',
        postgresql_ops={'created_at': 'DESC'}
    )

    # Performance indexes dla workflow_executions table
    op.create_index(
        'idx_executions_workflow_status',
        'workflow_executions',
        ['workflow_id', 'status']
    )

    op.create_index(
        'idx_executions_running',
        'workflow_executions',
        ['status', 'started_at'],
        postgresql_where=sa.text("status IN ('pending', 'running')"),
        postgresql_using='btree'
    )

    # Composite index dla execution history queries
    op.create_index(
        'idx_executions_workflow_started',
        'workflow_executions',
        ['workflow_id', 'started_at'],
        postgresql_ops={'started_at': 'DESC'}
    )


def downgrade():
    """Usuwa indeksy wydajnościowe."""
    op.drop_index('idx_executions_workflow_started', table_name='workflow_executions')
    op.drop_index('idx_executions_running', table_name='workflow_executions')
    op.drop_index('idx_executions_workflow_status', table_name='workflow_executions')
    op.drop_index('idx_workflows_owner_created', table_name='workflows')
    op.drop_index('idx_workflows_project_status', table_name='workflows')
