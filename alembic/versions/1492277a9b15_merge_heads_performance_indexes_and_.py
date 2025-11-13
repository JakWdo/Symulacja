"""merge heads: performance indexes and enum fix

Revision ID: 1492277a9b15
Revises: 20251112_perf_idx, 20251112_force_v2
Create Date: 2025-11-13 12:24:52.696555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1492277a9b15'
down_revision: Union[str, Sequence[str], None] = ('20251112_perf_idx', '20251112_force_v2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
