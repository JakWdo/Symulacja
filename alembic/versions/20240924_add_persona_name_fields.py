"""add persona name and headline fields

Revision ID: 20240924_add_persona_name_fields
Revises: ce931cd98f6c
Create Date: 2024-09-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240924_add_persona_name_fields'
down_revision = 'ce931cd98f6c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('personas', sa.Column('full_name', sa.String(length=150), nullable=True))
    op.add_column('personas', sa.Column('persona_title', sa.String(length=150), nullable=True))
    op.add_column('personas', sa.Column('headline', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('personas', 'headline')
    op.drop_column('personas', 'persona_title')
    op.drop_column('personas', 'full_name')
