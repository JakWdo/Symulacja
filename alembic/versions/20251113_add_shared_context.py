"""add shared context (environments, tags, filters, snapshots)

Revision ID: 20251113_shared_context
Revises: 20251113_teams
Create Date: 2025-11-13 16:00:00.000000

Adds Shared Context infrastructure (Faza 2):
- environments table (team-level workspaces for shared resources)
- tags table (semantic tagging with facets: dem, geo, psy, biz, ctx, custom)
- resource_tags table (many-to-many for tagging personas/workflows/etc.)
- saved_filters table (reusable DSL filter queries)
- project_snapshots table (immutable resource sets for reproducibility)
- environment_id columns in projects, personas, workflows

This migration enables:
- Shared persona/workflow pools across projects within teams
- Faceted filtering and tagging
- Reproducible research through snapshots
- Efficient resource reuse to reduce LLM API costs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251113_shared_context'
down_revision: Union[str, Sequence[str], None] = '20251113_teams'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add shared context infrastructure."""

    # 1. Create environments table
    op.create_table(
        'environments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for environments
    op.create_index('idx_environments_team_id', 'environments', ['team_id'], unique=False)
    op.create_index('idx_environments_is_active', 'environments', ['is_active'], unique=False)

    # 2. Create tags table (global tag registry)
    op.create_table(
        'tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('facet', sa.String(length=50), nullable=False),  # dem, geo, psy, biz, ctx, custom
        sa.Column('key', sa.String(length=100), nullable=False),   # age-25-34, warsaw, etc.
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facet', 'key', name='uq_tag_facet_key')  # Unique facet:key combination
    )

    # Indexes for tags (critical for filtering performance)
    op.create_index('idx_tags_facet', 'tags', ['facet'], unique=False)
    op.create_index('idx_tags_key', 'tags', ['key'], unique=False)

    # 3. Create resource_tags table (many-to-many for tagging resources)
    op.create_table(
        'resource_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),  # persona, workflow, etc.
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('environment_id', 'resource_type', 'resource_id', 'tag_id',
                          name='uq_resource_tag')  # Prevent duplicate tags on same resource
    )

    # Indexes for resource_tags (critical for filter queries)
    op.create_index('idx_resource_tags_environment_id', 'resource_tags', ['environment_id'], unique=False)
    op.create_index('idx_resource_tags_resource_type', 'resource_tags', ['resource_type'], unique=False)
    op.create_index('idx_resource_tags_resource_id', 'resource_tags', ['resource_id'], unique=False)
    op.create_index('idx_resource_tags_tag_id', 'resource_tags', ['tag_id'], unique=False)
    # Composite index for filtering by type within environment
    op.create_index('idx_resource_tags_env_type', 'resource_tags',
                   ['environment_id', 'resource_type'], unique=False)

    # 4. Create saved_filters table (reusable DSL queries)
    op.create_table(
        'saved_filters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('dsl', sa.Text(), nullable=False),  # DSL query string
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for saved_filters
    op.create_index('idx_saved_filters_environment_id', 'saved_filters', ['environment_id'], unique=False)
    op.create_index('idx_saved_filters_created_by', 'saved_filters', ['created_by'], unique=False)

    # 5. Create project_snapshots table (immutable resource sets)
    op.create_table(
        'project_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),  # persona, workflow, etc.
        sa.Column('resource_ids', postgresql.JSONB(), nullable=False),  # Array of UUIDs
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for project_snapshots
    op.create_index('idx_project_snapshots_project_id', 'project_snapshots', ['project_id'], unique=False)
    op.create_index('idx_project_snapshots_resource_type', 'project_snapshots', ['resource_type'], unique=False)

    # 6. Add environment_id to projects table
    # Nullable at first - will be filled by backfill script
    op.add_column('projects', sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add FK constraint
    op.create_foreign_key(
        'fk_projects_environment_id',
        'projects', 'environments',
        ['environment_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for project environment lookups
    op.create_index('idx_projects_environment_id', 'projects', ['environment_id'], unique=False)

    # 7. Add environment_id to personas table
    # Nullable at first - will be filled by backfill script
    op.add_column('personas', sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add FK constraint
    op.create_foreign_key(
        'fk_personas_environment_id',
        'personas', 'environments',
        ['environment_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for persona environment lookups (critical for filtering)
    op.create_index('idx_personas_environment_id', 'personas', ['environment_id'], unique=False)

    # 8. Add environment_id to workflows table
    # Nullable at first - will be filled by backfill script
    op.add_column('workflows', sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add FK constraint
    op.create_foreign_key(
        'fk_workflows_environment_id',
        'workflows', 'environments',
        ['environment_id'], ['id'],
        ondelete='SET NULL'
    )

    # Index for workflow environment lookups
    op.create_index('idx_workflows_environment_id', 'workflows', ['environment_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove shared context infrastructure."""

    # 1. Drop environment_id from workflows
    op.drop_index('idx_workflows_environment_id', table_name='workflows')
    op.drop_constraint('fk_workflows_environment_id', 'workflows', type_='foreignkey')
    op.drop_column('workflows', 'environment_id')

    # 2. Drop environment_id from personas
    op.drop_index('idx_personas_environment_id', table_name='personas')
    op.drop_constraint('fk_personas_environment_id', 'personas', type_='foreignkey')
    op.drop_column('personas', 'environment_id')

    # 3. Drop environment_id from projects
    op.drop_index('idx_projects_environment_id', table_name='projects')
    op.drop_constraint('fk_projects_environment_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'environment_id')

    # 4. Drop project_snapshots
    op.drop_index('idx_project_snapshots_resource_type', table_name='project_snapshots')
    op.drop_index('idx_project_snapshots_project_id', table_name='project_snapshots')
    op.drop_table('project_snapshots')

    # 5. Drop saved_filters
    op.drop_index('idx_saved_filters_created_by', table_name='saved_filters')
    op.drop_index('idx_saved_filters_environment_id', table_name='saved_filters')
    op.drop_table('saved_filters')

    # 6. Drop resource_tags
    op.drop_index('idx_resource_tags_env_type', table_name='resource_tags')
    op.drop_index('idx_resource_tags_tag_id', table_name='resource_tags')
    op.drop_index('idx_resource_tags_resource_id', table_name='resource_tags')
    op.drop_index('idx_resource_tags_resource_type', table_name='resource_tags')
    op.drop_index('idx_resource_tags_environment_id', table_name='resource_tags')
    op.drop_table('resource_tags')

    # 7. Drop tags
    op.drop_index('idx_tags_key', table_name='tags')
    op.drop_index('idx_tags_facet', table_name='tags')
    op.drop_table('tags')

    # 8. Drop environments
    op.drop_index('idx_environments_is_active', table_name='environments')
    op.drop_index('idx_environments_team_id', table_name='environments')
    op.drop_table('environments')
