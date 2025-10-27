"""add persona metadata (needs, audit, soft delete)

Revision ID: 20251027_persona_metadata
Revises: 20251015_segment_tracking
Create Date: 2025-10-27

Konsolidacja metadanych persony:
- needs_and_pains (JSONB) - JTBD analysis
- deleted_at, deleted_by - soft delete
- persona_audit_log table - audit trail
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251027_persona_metadata'
down_revision: Union[str, Sequence[str], None] = '20251015_segment_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add persona metadata fields and audit log table."""

    # === DODAJ JSONB COLUMN DLA NEEDS & PAINS ===
    op.add_column('personas', sa.Column('needs_and_pains', postgresql.JSONB, nullable=True))

    # === DODAJ SOFT DELETE METADATA ===
    op.add_column('personas', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'personas',
        sa.Column(
            'deleted_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        )
    )

    # === UTWÓRZ TABELĘ PERSONA_AUDIT_LOG ===
    op.create_table(
        'persona_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', postgresql.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )

    # === DODAJ INDEXES DLA PERFORMANCE ===
    # Soft delete indexes
    op.create_index('idx_persona_deleted_at', 'personas', ['deleted_at'])
    op.create_index('idx_persona_deleted_by', 'personas', ['deleted_by'])

    # Audit log indexes
    op.create_index('idx_audit_persona_id', 'persona_audit_log', ['persona_id'])
    op.create_index('idx_audit_user_id', 'persona_audit_log', ['user_id'])
    op.create_index('idx_audit_action', 'persona_audit_log', ['action'])
    op.create_index('idx_audit_timestamp', 'persona_audit_log', ['timestamp'])

    # Composite index dla common query pattern (persona + timestamp DESC)
    op.create_index(
        'idx_audit_persona_time_desc',
        'persona_audit_log',
        ['persona_id', sa.text('timestamp DESC')]
    )


def downgrade():
    """Remove persona metadata fields and audit log table."""
    # Drop indexes
    op.drop_index('idx_audit_persona_time_desc', table_name='persona_audit_log')
    op.drop_index('idx_audit_timestamp', table_name='persona_audit_log')
    op.drop_index('idx_audit_action', table_name='persona_audit_log')
    op.drop_index('idx_audit_user_id', table_name='persona_audit_log')
    op.drop_index('idx_audit_persona_id', table_name='persona_audit_log')
    op.drop_index('idx_persona_deleted_by', table_name='personas')
    op.drop_index('idx_persona_deleted_at', table_name='personas')

    # Drop table
    op.drop_table('persona_audit_log')

    # Drop columns
    op.drop_column('personas', 'deleted_by')
    op.drop_column('personas', 'deleted_at')
    op.drop_column('personas', 'needs_and_pains')
