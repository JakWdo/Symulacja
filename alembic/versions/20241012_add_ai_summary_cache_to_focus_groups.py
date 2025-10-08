"""add ai_summary cache to focus groups

Revision ID: f3e2f6823b9e
Revises: e06a13d1dfb4_add_target_participants_to_focus_groups
Create Date: 2024-10-12 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f3e2f6823b9e"
down_revision: Union[str, None] = "e06a13d1dfb4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("focus_groups", sa.Column("ai_summary", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("focus_groups", "ai_summary")
