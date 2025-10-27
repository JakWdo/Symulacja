"""add soft delete to projects

Revision ID: 20251027_project_soft_delete
Revises: 20251027_persona_metadata
Create Date: 2025-10-27

Dodaje soft delete metadata do projektów:
- deleted_at (timestamp usunięcia)
- deleted_by (UUID użytkownika który usunął projekt)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251027_project_soft_delete'
down_revision: Union[str, Sequence[str], None] = '20251027_persona_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add soft delete metadata to projects table."""

    # === DODAJ SOFT DELETE METADATA ===
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'projects',
        sa.Column(
            'deleted_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        )
    )


def downgrade():
    """Remove soft delete metadata from projects table."""

    op.drop_column('projects', 'deleted_by')
    op.drop_column('projects', 'deleted_at')
