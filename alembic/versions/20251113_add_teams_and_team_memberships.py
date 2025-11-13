"""add teams and team memberships

Revision ID: 20251113_teams
Revises: 009254ee5182
Create Date: 2025-11-13 15:00:00.000000

Adds RBAC + Team Accounts:
- teams table (team workspace)
- team_memberships table (user-team associations with roles)
- projects.team_id (FK to teams)

This migration enables team-based collaboration and fine-grained access control.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251113_teams'
down_revision: Union[str, Sequence[str], None] = '009254ee5182'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add teams and team memberships (idempotent)."""

    # Check if migration already applied
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # If teams table already exists, skip this migration
    if 'teams' in existing_tables:
        print("⚠️  Teams tables already exist - skipping migration")
        return

    # 1. Create team_role_enum for role_in_team (idempotent - skip if exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE team_role_enum AS ENUM ('owner', 'member', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Create teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Index for active teams lookup
    op.create_index('idx_teams_is_active', 'teams', ['is_active'], unique=False)

    # 3. Create team_memberships table
    op.create_table(
        'team_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_in_team', sa.Enum('owner', 'member', 'viewer', name='team_role_enum', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'user_id', name='uq_team_user')  # User can only be in team once
    )

    # Indexes for team_memberships (critical for performance)
    op.create_index('idx_team_memberships_team_id', 'team_memberships', ['team_id'], unique=False)
    op.create_index('idx_team_memberships_user_id', 'team_memberships', ['user_id'], unique=False)
    op.create_index('idx_team_memberships_role', 'team_memberships', ['role_in_team'], unique=False)

    # 4. Add team_id to projects table
    # Nullable at first - will be filled by backfill script
    op.add_column('projects', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Add FK constraint (nullable for now, will be made NOT NULL after backfill)
    op.create_foreign_key(
        'fk_projects_team_id',
        'projects', 'teams',
        ['team_id'], ['id'],
        ondelete='CASCADE'
    )

    # Index for project team lookups (critical for scoping queries)
    op.create_index('idx_projects_team_id', 'projects', ['team_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove teams and team memberships."""

    # 1. Drop projects.team_id and its constraints
    op.drop_index('idx_projects_team_id', table_name='projects')
    op.drop_constraint('fk_projects_team_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'team_id')

    # 2. Drop team_memberships indexes
    op.drop_index('idx_team_memberships_role', table_name='team_memberships')
    op.drop_index('idx_team_memberships_user_id', table_name='team_memberships')
    op.drop_index('idx_team_memberships_team_id', table_name='team_memberships')

    # 3. Drop team_memberships table
    op.drop_table('team_memberships')

    # 4. Drop teams indexes
    op.drop_index('idx_teams_is_active', table_name='teams')

    # 5. Drop teams table
    op.drop_table('teams')

    # 6. Drop team_role_enum
    op.execute("DROP TYPE team_role_enum")
