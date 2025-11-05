"""extend_workflow_node_types_and_add_template_support

Dodaje wsparcie dla:
1. 14 typów węzłów workflow (rozszerza z 3 do 14)
2. Pole is_template w workflows dla Template Library
3. CHECK constraints dla walidacji enum values
4. Indeksy dla optymalizacji queries
5. Data migration dla starych step_types

Revision ID: 45c8ede416fb
Revises: 4bdf0d123032
Create Date: 2025-11-04 14:03:55.066209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45c8ede416fb'
down_revision: Union[str, Sequence[str], None] = '4bdf0d123032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema - dodaje is_template, CHECK constraints i nowe typy węzłów.
    """
    # 1. Dodaj pole is_template do workflows
    op.add_column(
        'workflows',
        sa.Column(
            'is_template',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )

    # 2. Data migration - migruj stare step_types na nowe
    # Stare wartości: 'goal' → 'create-project'
    #                 'persona' → 'generate-personas'
    #                 'focus-group' → 'run-focus-group'
    op.execute("""
        UPDATE workflow_steps
        SET step_type = CASE
            WHEN step_type = 'goal' THEN 'create-project'
            WHEN step_type = 'persona' THEN 'generate-personas'
            WHEN step_type = 'focus-group' THEN 'run-focus-group'
            ELSE step_type
        END
        WHERE step_type IN ('goal', 'persona', 'focus-group')
    """)

    # 3. Dodaj CHECK constraints dla walidacji enum values

    # workflows.status: draft, active, archived
    op.create_check_constraint(
        'ck_workflows_status',
        'workflows',
        sa.text("status IN ('draft', 'active', 'archived')")
    )

    # workflow_executions.status: pending, running, completed, failed
    op.create_check_constraint(
        'ck_workflow_executions_status',
        'workflow_executions',
        sa.text("status IN ('pending', 'running', 'completed', 'failed')")
    )

    # workflow_steps.step_type: 14 typów węzłów
    op.create_check_constraint(
        'ck_workflow_steps_step_type',
        'workflow_steps',
        sa.text("""step_type IN (
            'start',
            'end',
            'create-project',
            'generate-personas',
            'create-survey',
            'run-focus-group',
            'analyze-results',
            'decision',
            'wait',
            'export-pdf',
            'webhook',
            'condition',
            'loop',
            'merge'
        )""")
    )

    # 4. Dodaj indeksy dla optymalizacji queries
    op.create_index(
        'idx_workflows_is_template',
        'workflows',
        ['is_template']
    )
    op.create_index(
        'idx_workflows_created_at',
        'workflows',
        ['created_at']
    )
    op.create_index(
        'idx_workflow_executions_created_at',
        'workflow_executions',
        ['created_at']
    )


def downgrade() -> None:
    """
    Downgrade schema - usuwa is_template, CHECK constraints i indeksy.
    """
    # 1. Usuń indeksy
    op.drop_index('idx_workflow_executions_created_at', table_name='workflow_executions')
    op.drop_index('idx_workflows_created_at', table_name='workflows')
    op.drop_index('idx_workflows_is_template', table_name='workflows')

    # 2. Usuń CHECK constraints
    op.drop_constraint('ck_workflow_steps_step_type', 'workflow_steps', type_='check')
    op.drop_constraint('ck_workflow_executions_status', 'workflow_executions', type_='check')
    op.drop_constraint('ck_workflows_status', 'workflows', type_='check')

    # 3. Data migration - przywróć stare step_types
    op.execute("""
        UPDATE workflow_steps
        SET step_type = CASE
            WHEN step_type = 'create-project' THEN 'goal'
            WHEN step_type = 'generate-personas' THEN 'persona'
            WHEN step_type = 'run-focus-group' THEN 'focus-group'
            ELSE step_type
        END
        WHERE step_type IN ('create-project', 'generate-personas', 'run-focus-group')
    """)

    # 4. Usuń kolumnę is_template
    op.drop_column('workflows', 'is_template')
