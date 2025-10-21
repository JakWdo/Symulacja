"""add persona delete metadata

Revision ID: 20251016_add_persona_delete_metadata
Revises: 20251016_persona_details
Create Date: 2025-10-16

Dodaje metadane usunięcia persony (deleted_at, deleted_by) oraz indeksy pomocnicze.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251016_add_persona_del_meta"
down_revision = "20251016_persona_details"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "personas",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "personas",
        sa.Column(
            "deleted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_persona_deleted_at", "personas", ["deleted_at"])
    op.create_index("idx_persona_deleted_by", "personas", ["deleted_by"])


def downgrade():
    op.drop_index("idx_persona_deleted_by", table_name="personas")
    op.drop_index("idx_persona_deleted_at", table_name="personas")
    op.drop_column("personas", "deleted_by")
    op.drop_column("personas", "deleted_at")
