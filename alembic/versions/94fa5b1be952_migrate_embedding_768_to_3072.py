"""migrate_embedding_768_to_3072

Revision ID: 94fa5b1be952
Revises: 20251016_remove_kpi_journey
Create Date: 2025-10-23 13:30:08.317043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94fa5b1be952'
down_revision: Union[str, Sequence[str], None] = '20251016_remove_kpi_journey'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - migrate embedding column from vector(768) to vector(3072).

    This migration is necessary because we switched from sentence-transformers (768-dim)
    to Google Gemini embeddings (3072-dim).

    Strategy:
    1. Clear existing embeddings (old 768-dim are incompatible with new model)
    2. Change column type to vector(3072)
    3. Future PersonaEvents will use Gemini 3072-dim embeddings
    """
    # Step 1: Clear existing embeddings (old model incompatible with new)
    # This is safe because embeddings can be regenerated if needed
    op.execute("UPDATE persona_events SET embedding = NULL WHERE embedding IS NOT NULL")

    # Step 2: Alter column type from vector(768) to vector(3072)
    # PostgreSQL requires explicit cast even though we set NULL above
    op.execute("""
        ALTER TABLE persona_events
        ALTER COLUMN embedding TYPE vector(3072)
        USING embedding::vector(3072)
    """)


def downgrade() -> None:
    """Downgrade schema - revert to vector(768).

    WARNING: This will truncate embeddings from 3072 to 768 dimensions,
    losing information. Only use for rollback scenarios.
    """
    # Clear embeddings first (3072-dim can't fit into 768-dim)
    op.execute("UPDATE persona_events SET embedding = NULL WHERE embedding IS NOT NULL")

    # Revert column type to vector(768)
    op.execute("""
        ALTER TABLE persona_events
        ALTER COLUMN embedding TYPE vector(768)
        USING embedding::vector(768)
    """)
