"""add system_role enum for RBAC

Revision ID: a1b2c3d4e5f6
Revises: fa9c9d3c0ee4
Create Date: 2025-11-12 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fa9c9d3c0ee4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add system_role ENUM column to users for role-based access control."""

    # Create ENUM type for system roles
    system_role_enum = postgresql.ENUM(
        'admin',
        'researcher',
        'viewer',
        name='system_role_enum',
        create_type=True
    )
    system_role_enum.create(op.get_bind(), checkfirst=True)

    # Check if column already exists (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'system_role' not in columns:
        # Add system_role column (nullable, default NULL initially)
        op.add_column(
            'users',
            sa.Column(
                'system_role',
                system_role_enum,
                nullable=True,
                server_default=None
            )
        )

        # Set default 'researcher' for existing users
        op.execute("UPDATE users SET system_role = 'researcher' WHERE system_role IS NULL")

        # Make column NOT NULL after setting defaults
        op.alter_column('users', 'system_role', nullable=False, server_default='researcher')


def downgrade() -> None:
    """Remove system_role column and ENUM type."""

    # Drop system_role column if exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'system_role' in columns:
        op.drop_column('users', 'system_role')

    # Drop ENUM type
    system_role_enum = postgresql.ENUM(
        'admin',
        'researcher',
        'viewer',
        name='system_role_enum'
    )
    system_role_enum.drop(op.get_bind(), checkfirst=True)
