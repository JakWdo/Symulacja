"""add_study_designer_chat_models

Revision ID: 8ba3d04beee1
Revises: 45c8ede416fb
Create Date: 2025-11-08 17:00:00.000000

Adds tables for Study Designer Chat feature:
- study_designer_sessions: Interactive study design sessions
- study_designer_messages: Conversation messages (user/assistant/system)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8ba3d04beee1'
down_revision: Union[str, Sequence[str], None] = '45c8ede416fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create study_designer_sessions table
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

    # Create indexes for study_designer_sessions
    op.create_index('idx_study_designer_sessions_user_id', 'study_designer_sessions', ['user_id'], unique=False)
    op.create_index('idx_study_designer_sessions_status', 'study_designer_sessions', ['status'], unique=False)
    op.create_index('idx_study_designer_sessions_created_at', 'study_designer_sessions', ['created_at'], unique=False)

    # Create study_designer_messages table
    op.create_table(
        'study_designer_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'{}'::json"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['study_designer_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for study_designer_messages
    op.create_index('idx_study_designer_messages_session_id', 'study_designer_messages', ['session_id'], unique=False)
    op.create_index('idx_study_designer_messages_created_at', 'study_designer_messages', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_study_designer_messages_created_at', table_name='study_designer_messages')
    op.drop_index('idx_study_designer_messages_session_id', table_name='study_designer_messages')

    # Drop tables
    op.drop_table('study_designer_messages')

    op.drop_index('idx_study_designer_sessions_created_at', table_name='study_designer_sessions')
    op.drop_index('idx_study_designer_sessions_status', table_name='study_designer_sessions')
    op.drop_index('idx_study_designer_sessions_user_id', table_name='study_designer_sessions')

    op.drop_table('study_designer_sessions')
