"""add_persona_details_mvp

Revision ID: 20251016_persona_details
Revises: 20251015_segment_tracking
Create Date: 2025-10-16

Dodaje funkcjonalność Szczegółowego Widoku Persony (MVP):
- JSONB columns dla KPI snapshot, customer journey, needs & pains
- Tabela persona_audit_log dla audit trail
- Indexes dla performance
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251016_persona_details'
down_revision = '20251015_segment_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # === DODAJ JSONB COLUMNS DO PERSONAS ===
    op.add_column('personas', sa.Column('kpi_snapshot', postgresql.JSONB, nullable=True))
    op.add_column('personas', sa.Column('customer_journey', postgresql.JSONB, nullable=True))
    op.add_column('personas', sa.Column('needs_and_pains', postgresql.JSONB, nullable=True))

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
    # Indexes dla persona_audit_log
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

    # GIN indexes dla JSONB fields (umożliwiają query'owanie po nested fields)
    op.create_index(
        'idx_persona_kpi_snapshot_gin',
        'personas',
        ['kpi_snapshot'],
        postgresql_using='gin'
    )


def downgrade():
    # Drop indexes
    op.drop_index('idx_persona_kpi_snapshot_gin', table_name='personas')
    op.drop_index('idx_audit_persona_time_desc', table_name='persona_audit_log')
    op.drop_index('idx_audit_timestamp', table_name='persona_audit_log')
    op.drop_index('idx_audit_action', table_name='persona_audit_log')
    op.drop_index('idx_audit_user_id', table_name='persona_audit_log')
    op.drop_index('idx_audit_persona_id', table_name='persona_audit_log')

    # Drop table
    op.drop_table('persona_audit_log')

    # Drop columns
    op.drop_column('personas', 'needs_and_pains')
    op.drop_column('personas', 'customer_journey')
    op.drop_column('personas', 'kpi_snapshot')
