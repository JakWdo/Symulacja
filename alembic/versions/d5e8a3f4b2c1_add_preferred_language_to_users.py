"""add preferred_language to users

Revision ID: d5e8a3f4b2c1
Revises: ca8ee02c29a1
Create Date: 2025-10-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5e8a3f4b2c1'
down_revision: Union[str, Sequence[str], None] = 'ca8ee02c29a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add preferred_language column to users table.

    This migration adds support for user language preferences (PL/EN).
    Uses idempotent checks to ensure safe execution.
    """
    # Get connection and inspect existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    # Add preferred_language column if it doesn't exist
    if 'preferred_language' not in columns:
        op.add_column('users', sa.Column('preferred_language', sa.String(5), nullable=False, server_default='pl'))

        # Create index for better query performance
        op.create_index('ix_users_preferred_language', 'users', ['preferred_language'], unique=False)


def downgrade() -> None:
    """Remove preferred_language column from users table."""
    op.drop_index('ix_users_preferred_language', table_name='users')
    op.drop_column('users', 'preferred_language')
