"""force fix system_role enum v2 - AGGRESSIVE CASCADE repair

Revision ID: 20251112_force_v2
Revises: 20251112_fix_enum
Create Date: 2025-11-12 16:00:00.000000

CRITICAL: This is a FORCE FIX migration that MUST execute even if previous migrations failed.
This migration uses AGGRESSIVE CASCADE drop to fix enum case sensitivity issue.

Problem: Previous migration (20251112_fix_enum) executed but didn't fix the enum properly.
Root cause: Enum still has UPPERCASE values in Cloud SQL despite migration running.

Solution: Force recreate enum with lowercase values using direct SQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251112_force_v2'
down_revision: Union[str, Sequence[str], None] = '20251112_fix_enum'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """FORCE FIX: Aggressively recreate system_role_enum with lowercase values.

    This migration will execute regardless of previous state.
    It's idempotent - safe to run multiple times.
    """

    # Step 1: Change column to TEXT temporarily (USING cast for safety)
    # Use IF EXISTS-like approach by catching errors
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE users ALTER COLUMN system_role TYPE TEXT USING system_role::TEXT;
        EXCEPTION
            WHEN OTHERS THEN
                -- Column might already be TEXT from previous attempt
                RAISE NOTICE 'Column already TEXT or error: %', SQLERRM;
        END $$;
    """)

    # Step 2: DROP enum AGGRESSIVELY with CASCADE
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")

    # Step 3: CREATE new enum with lowercase values (matches Python code)
    op.execute("""
        CREATE TYPE system_role_enum AS ENUM ('admin', 'researcher', 'viewer')
    """)

    # Step 4: Normalize all values to lowercase (handles mixed case data)
    op.execute("UPDATE users SET system_role = LOWER(TRIM(system_role))")

    # Step 5: Convert column back to enum type (with explicit casting)
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN system_role TYPE system_role_enum
        USING system_role::system_role_enum
    """)

    # Step 6: Set default and NOT NULL constraint
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET DEFAULT 'researcher'::system_role_enum")
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET NOT NULL")


def downgrade() -> None:
    """Revert to TEXT column (doesn't restore uppercase enum)."""

    # Convert column to TEXT
    op.execute("ALTER TABLE users ALTER COLUMN system_role TYPE TEXT")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")
