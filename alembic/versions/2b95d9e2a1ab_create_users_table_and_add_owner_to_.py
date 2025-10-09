from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = '2b95d9e2a1ab'
down_revision: Union[str, Sequence[str], None] = 'f3e2f6823b9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create users table and add owner_id to projects."""

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('encrypted_google_api_key', sa.Text, nullable=True),
        sa.Column('email_notifications_enabled', sa.Boolean, default=True),
        sa.Column('discussion_complete_notifications', sa.Boolean, default=True),
        sa.Column('weekly_reports_enabled', sa.Boolean, default=False),
        sa.Column('system_updates_notifications', sa.Boolean, default=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('plan', sa.String(50), default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on email
    op.create_index('idx_users_email', 'users', ['email'])

    # Add owner_id to projects table (nullable first, we'll fill it and make it required)
    op.add_column('projects', sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create default user for existing projects (hasło: "changeme")
    # Hasło hash: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lkqKmLqHvzGK
    default_user_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO users (id, email, hashed_password, full_name, plan, is_active, created_at, updated_at)
        VALUES (
            '{default_user_id}',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lkqKmLqHvzGK',
            'Default Admin',
            'enterprise',
            true,
            NOW(),
            NOW()
        )
    """)

    # Assign existing projects to default user
    op.execute(f"""
        UPDATE projects SET owner_id = '{default_user_id}' WHERE owner_id IS NULL
    """)

    # Now make owner_id NOT NULL
    op.alter_column('projects', 'owner_id', nullable=False)

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_projects_owner_id',
        'projects',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Create index on owner_id for faster queries
    op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])


def downgrade() -> None:
    """Downgrade schema: remove owner_id from projects and drop users table."""

    # Drop index and foreign key from projects
    op.drop_index('idx_projects_owner_id', 'projects')
    op.drop_constraint('fk_projects_owner_id', 'projects', type_='foreignkey')

    # Drop owner_id column from projects
    op.drop_column('projects', 'owner_id')

    # Drop users table index and table
    op.drop_index('idx_users_email', 'users')
    op.drop_table('users')
