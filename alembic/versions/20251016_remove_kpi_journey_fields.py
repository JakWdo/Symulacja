"""remove kpi_snapshot and customer_journey from personas

Revision ID: 20251016_remove_kpi_journey
Revises: 20251016_add_persona_del_meta
Create Date: 2025-10-16

Usuwa deprecated pola kpi_snapshot i customer_journey z tabeli personas.
Te pola zostały zastąpione przez dedykowane serwisy:
- KPI metrics → persona_kpi_service (real-time calculation)
- Customer journey → persona_journey_service (on-demand generation)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251016_remove_kpi_journey"
down_revision = "20251016_add_persona_del_meta"
branch_labels = None
depends_on = None


def upgrade():
    # Drop GIN index on kpi_snapshot (from previous migration)
    op.drop_index("idx_persona_kpi_snapshot_gin", table_name="personas")

    # Drop deprecated JSONB columns
    op.drop_column("personas", "customer_journey")
    op.drop_column("personas", "kpi_snapshot")


def downgrade():
    # Re-add columns (nullable, no data restoration)
    op.add_column(
        "personas",
        sa.Column("kpi_snapshot", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column("customer_journey", postgresql.JSONB, nullable=True),
    )

    # Re-create GIN index for kpi_snapshot
    op.create_index(
        "idx_persona_kpi_snapshot_gin",
        "personas",
        ["kpi_snapshot"],
        postgresql_using="gin",
    )
