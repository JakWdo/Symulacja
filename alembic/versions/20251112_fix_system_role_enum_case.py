"""fix system_role_enum case sensitivity (uppercase → lowercase)

Revision ID: 20251112_fix_enum
Revises: 17b431ef8acc
Create Date: 2025-11-12 16:00:00.000000

Problem: Cloud SQL ma enum z uppercase wartościami (ADMIN, RESEARCHER, VIEWER)
ale kod oczekuje lowercase ('admin', 'researcher', 'viewer').
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251112_fix_enum'
down_revision: Union[str, Sequence[str], None] = '17b431ef8acc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix system_role_enum to use lowercase values.

    AGGRESSIVE FIX: This migration forcefully recreates the enum with lowercase values.
    """

    # Step 1: Zmień kolumnę system_role na TEXT tymczasowo (USING cast dla bezpieczeństwa)
    op.execute("ALTER TABLE users ALTER COLUMN system_role TYPE TEXT USING system_role::TEXT")

    # Step 2: Usuń stary enum AGRESYWNIE (CASCADE usuwa wszystkie zależności)
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")

    # Step 3: Utwórz nowy enum z lowercase wartościami (zgodnie z kodem)
    # Używamy bezpośredniego SQL zamiast SQLAlchemy bo mamy pełną kontrolę
    op.execute("""
        CREATE TYPE system_role_enum AS ENUM ('admin', 'researcher', 'viewer')
    """)

    # Step 4: Konwertuj wszystkie wartości na lowercase (normalizacja)
    op.execute("UPDATE users SET system_role = LOWER(TRIM(system_role))")

    # Step 5: Przywróć kolumnę do typu enum (z explicit casting)
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN system_role TYPE system_role_enum
        USING system_role::system_role_enum
    """)

    # Step 6: Ustaw default i NOT NULL
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET DEFAULT 'researcher'::system_role_enum")
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET NOT NULL")


def downgrade() -> None:
    """Revert to TEXT column (nie przywracamy uppercase enum)."""

    # Nie ma sensu wracać do uppercase - downgrade zamienia na TEXT
    op.execute("ALTER TABLE users ALTER COLUMN system_role TYPE TEXT")
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")
