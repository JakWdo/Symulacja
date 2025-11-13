"""remove_study_designer_tables

Revision ID: 009254ee5182
Revises: 1492277a9b15
Create Date: 2025-11-13 14:54:52.275130

Removes Study Designer tables:
- study_designer_messages
- study_designer_sessions

Study Designer feature has been archived and replaced with Product Assistant.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '009254ee5182'
down_revision: Union[str, Sequence[str], None] = '1492277a9b15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - remove Study Designer tables."""
    # Drop indexes first
    op.drop_index('idx_study_designer_messages_created_at', table_name='study_designer_messages')
    op.drop_index('idx_study_designer_messages_session_id', table_name='study_designer_messages')

    # Drop messages table (has FK to sessions)
    op.drop_table('study_designer_messages')

    # Drop indexes for sessions
    op.drop_index('idx_study_designer_sessions_created_at', table_name='study_designer_sessions')
    op.drop_index('idx_study_designer_sessions_status', table_name='study_designer_sessions')
    op.drop_index('idx_study_designer_sessions_user_id', table_name='study_designer_sessions')

    # Drop sessions table
    op.drop_table('study_designer_sessions')


def downgrade() -> None:
    """Downgrade schema - recreate Study Designer tables."""
    # Recreate study_designer_sessions table
    op.create_table(
        'study_designer_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'active'"), nullable=False),
        sa.Column('current_stage', sa.String(length=50), server_default=sa.text("'welcome'"), nullable=False),
        sa.Column('conversation_state', postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column('generated_plan', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_workflow_id'], ['workflows.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate indexes for sessions
    op.create_index('idx_study_designer_sessions_user_id', 'study_designer_sessions', ['user_id'], unique=False)
    op.create_index('idx_study_designer_sessions_status', 'study_designer_sessions', ['status'], unique=False)
    op.create_index('idx_study_designer_sessions_created_at', 'study_designer_sessions', ['created_at'], unique=False)

    # Recreate study_designer_messages table
    op.create_table(
        'study_designer_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'{}'::json"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['study_designer_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Recreate indexes for messages
    op.create_index('idx_study_designer_messages_session_id', 'study_designer_messages', ['session_id'], unique=False)
    op.create_index('idx_study_designer_messages_created_at', 'study_designer_messages', ['created_at'], unique=False)
