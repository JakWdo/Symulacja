"""add_country_to_persona

Revision ID: 93c93945d2a6
Revises: 9755d61029ad
Create Date: 2025-10-03 10:46:25.628232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93c93945d2a6'
down_revision: Union[str, Sequence[str], None] = '9755d61029ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('personas', sa.Column('country', sa.String(100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('personas', 'country')
