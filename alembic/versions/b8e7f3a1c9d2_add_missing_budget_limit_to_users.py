"""add missing budget_limit to users

Revision ID: b8e7f3a1c9d2
Revises: fa9c9d3c0ee4
Create Date: 2025-10-28 13:21:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b8e7f3a1c9d2'
down_revision: Union[str, Sequence[str], None] = 'fa9c9d3c0ee4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing budget_limit column to users table.

    This migration adds the budget_limit column that was accidentally omitted
    from migration fa9c9d3c0ee4. It uses idempotent checks to ensure it can
    be safely run multiple times.
    """
    # Get connection and inspect existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    # Add budget_limit column if it doesn't exist
    if 'budget_limit' not in columns:
        op.add_column('users', sa.Column('budget_limit', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove budget_limit column from users table."""
    op.drop_column('users', 'budget_limit')
