"""add LLM provider preferences

Revision ID: 20251113_llm_prefs
Revises: 20251113_shared_context
Create Date: 2025-11-13 21:00:00.000000

Adds LLM Provider Preferences:
- users.preferred_llm_provider ENUM (google, openai, anthropic, azure_openai)
- users.preferred_model VARCHAR (optional override dla default model)
- projects.llm_provider_override ENUM (project-specific override)
- projects.model_override VARCHAR (project-specific model override)

This migration enables:
- Multi-provider support (Google Gemini, OpenAI, Anthropic, Azure OpenAI)
- User-level default LLM preferences
- Project-level LLM overrides (flexibility per project)
- Vendor lock-in risk reduction
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251113_llm_prefs'
down_revision: Union[str, Sequence[str], None] = '20251113_shared_context'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add LLM provider preferences."""

    # Check if migration already applied
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Create llm_provider_enum type
    from sqlalchemy.dialects.postgresql import ENUM
    llm_provider_enum = ENUM(
        'google',
        'openai',
        'anthropic',
        'azure_openai',
        name='llm_provider_enum',
        create_type=False
    )

    # Create ENUM explicitly with checkfirst=True (idempotent!)
    print("🔍 Checking if llm_provider_enum exists...")
    llm_provider_enum.create(conn, checkfirst=True)
    print("✅ llm_provider_enum ready")

    # 2. Add columns to users table
    users_columns = [col['name'] for col in inspector.get_columns('users')]

    if 'preferred_llm_provider' not in users_columns:
        print("Adding preferred_llm_provider to users...")
        op.add_column(
            'users',
            sa.Column(
                'preferred_llm_provider',
                llm_provider_enum,
                nullable=True,  # NULL = use system default
                server_default='google',  # Default to Google Gemini
            )
        )

    if 'preferred_model' not in users_columns:
        print("Adding preferred_model to users...")
        op.add_column(
            'users',
            sa.Column(
                'preferred_model',
                sa.String(length=100),
                nullable=True,  # NULL = use provider default
            )
        )

    # 3. Add columns to projects table
    projects_columns = [col['name'] for col in inspector.get_columns('projects')]

    if 'llm_provider_override' not in projects_columns:
        print("Adding llm_provider_override to projects...")
        op.add_column(
            'projects',
            sa.Column(
                'llm_provider_override',
                llm_provider_enum,
                nullable=True,  # NULL = use user preference or system default
            )
        )

    if 'model_override' not in projects_columns:
        print("Adding model_override to projects...")
        op.add_column(
            'projects',
            sa.Column(
                'model_override',
                sa.String(length=100),
                nullable=True,  # NULL = use user preference or provider default
            )
        )

    # 4. Create indexes for efficient filtering by provider
    print("Creating indexes for LLM provider queries...")

    try:
        op.create_index(
            'idx_users_preferred_llm_provider',
            'users',
            ['preferred_llm_provider'],
            unique=False
        )
    except Exception:
        print("⚠️ Index idx_users_preferred_llm_provider already exists")

    try:
        op.create_index(
            'idx_projects_llm_provider_override',
            'projects',
            ['llm_provider_override'],
            unique=False
        )
    except Exception:
        print("⚠️ Index idx_projects_llm_provider_override already exists")

    print("✅ LLM provider preferences migration completed")


def downgrade() -> None:
    """Downgrade schema - remove LLM provider preferences."""

    # Drop indexes
    op.drop_index('idx_projects_llm_provider_override', table_name='projects')
    op.drop_index('idx_users_preferred_llm_provider', table_name='users')

    # Drop columns
    op.drop_column('projects', 'model_override')
    op.drop_column('projects', 'llm_provider_override')
    op.drop_column('users', 'preferred_model')
    op.drop_column('users', 'preferred_llm_provider')

    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS llm_provider_enum")
