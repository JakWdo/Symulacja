"""merge multiple heads - study designer and rbac

Revision ID: 17b431ef8acc
Revises: 8ba3d04beee1, a1b2c3d4e5f6
Create Date: 2025-11-12 12:18:52.045769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17b431ef8acc'
down_revision: Union[str, Sequence[str], None] = ('8ba3d04beee1', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
