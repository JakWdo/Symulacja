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
    """Fix system_role_enum to use lowercase values."""

    # Step 1: Zmień kolumnę system_role na TEXT tymczasowo
    op.execute("ALTER TABLE users ALTER COLUMN system_role TYPE TEXT")

    # Step 2: Usuń stary enum (może być uppercase)
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")

    # Step 3: Utwórz nowy enum z lowercase wartościami (zgodnie z kodem)
    system_role_enum = postgresql.ENUM(
        'admin',
        'researcher',
        'viewer',
        name='system_role_enum',
        create_type=True
    )
    system_role_enum.create(op.get_bind(), checkfirst=True)

    # Step 4: Konwertuj wszystkie wartości na lowercase (na wypadek gdyby były mixed case)
    op.execute("UPDATE users SET system_role = LOWER(system_role)")

    # Step 5: Przywróć kolumnę do typu enum
    op.execute(
        "ALTER TABLE users ALTER COLUMN system_role TYPE system_role_enum "
        "USING system_role::system_role_enum"
    )

    # Step 6: Ustaw default
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET DEFAULT 'researcher'::system_role_enum")
    op.execute("ALTER TABLE users ALTER COLUMN system_role SET NOT NULL")


def downgrade() -> None:
    """Revert to TEXT column (nie przywracamy uppercase enum)."""

    # Nie ma sensu wracać do uppercase - downgrade zamienia na TEXT
    op.execute("ALTER TABLE users ALTER COLUMN system_role TYPE TEXT")
    op.execute("DROP TYPE IF EXISTS system_role_enum CASCADE")
