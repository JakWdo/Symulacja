"""add performance indexes for soft delete and filtering

Revision ID: 20251112_perf_idx
Revises: 18f44b7e6178
Create Date: 2025-11-12

Dodaje composite indexes dla optymalizacji najczęstszych zapytań:
- Personas: filtrowanie per projekt + soft delete status
- Projects: filtrowanie per owner + soft delete status
- FocusGroups: filtrowanie per projekt + status/soft delete

Cel wydajnościowy: Wszystkie zapytania <100ms p95
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251112_perf_idx'
down_revision = '18f44b7e6178'
branch_labels = None
depends_on = None


def upgrade():
    """
    Dodaje composite indexes dla optymalizacji zapytań z filtrami.

    Indeksy zoptymalizowane dla:
    1. Personas per projekt bez usuniętych: WHERE project_id = X AND deleted_at IS NULL
    2. Personas per projekt aktywne: WHERE project_id = X AND is_active = TRUE
    3. Projects per owner bez usuniętych: WHERE owner_id = X AND deleted_at IS NULL
    4. FocusGroups per projekt bez usuniętych: WHERE project_id = X AND deleted_at IS NULL
    5. FocusGroups per projekt + status: WHERE project_id = X AND status = 'completed'
    """

    # ============================================================================
    # PERSONAS TABLE INDEXES
    # ============================================================================

    # Composite index: project_id + deleted_at (najczęstsze zapytanie)
    # Używane w: lista person projektu, statystyki, dashboard
    # Przykład: SELECT * FROM personas WHERE project_id = X AND deleted_at IS NULL
    op.create_index(
        'idx_personas_project_deleted',
        'personas',
        ['project_id', 'deleted_at'],
        postgresql_using='btree'
    )

    # Composite index: project_id + is_active (alternatywny soft delete pattern)
    # Używane w: niektóre serwisy używają is_active zamiast deleted_at
    # Przykład: SELECT * FROM personas WHERE project_id = X AND is_active = TRUE
    op.create_index(
        'idx_personas_project_active',
        'personas',
        ['project_id', 'is_active'],
        postgresql_using='btree'
    )

    # Single index: deleted_at (używane w cleanup tasks)
    # Używane w: maintenance/cleanup_service.py
    # Przykład: DELETE FROM personas WHERE deleted_at < NOW() - INTERVAL '7 days'
    op.create_index(
        'idx_personas_deleted_at',
        'personas',
        ['deleted_at'],
        postgresql_using='btree',
        postgresql_where=sa.text('deleted_at IS NOT NULL')  # Partial index - tylko dla usuniętych
    )

    # ============================================================================
    # PROJECTS TABLE INDEXES
    # ============================================================================

    # Composite index: owner_id + deleted_at (filtrowanie projektów użytkownika)
    # Używane w: dashboard, lista projektów użytkownika
    # Przykład: SELECT * FROM projects WHERE owner_id = X AND deleted_at IS NULL
    op.create_index(
        'idx_projects_owner_deleted',
        'projects',
        ['owner_id', 'deleted_at'],
        postgresql_using='btree'
    )

    # Single index: deleted_at (używane w cleanup tasks)
    # Używane w: maintenance/cleanup_service.py
    # Przykład: DELETE FROM projects WHERE deleted_at < NOW() - INTERVAL '7 days'
    op.create_index(
        'idx_projects_deleted_at',
        'projects',
        ['deleted_at'],
        postgresql_using='btree',
        postgresql_where=sa.text('deleted_at IS NOT NULL')  # Partial index
    )

    # ============================================================================
    # FOCUS_GROUPS TABLE INDEXES
    # ============================================================================

    # Composite index: project_id + deleted_at (filtrowanie grup projektu)
    # Używane w: lista grup fokusowych projektu
    # Przykład: SELECT * FROM focus_groups WHERE project_id = X AND deleted_at IS NULL
    op.create_index(
        'idx_focus_groups_project_deleted',
        'focus_groups',
        ['project_id', 'deleted_at'],
        postgresql_using='btree'
    )

    # Composite index: project_id + status (monitoring statusu grup)
    # Używane w: dashboard, health checks, monitoring
    # Przykład: SELECT * FROM focus_groups WHERE project_id = X AND status = 'completed'
    op.create_index(
        'idx_focus_groups_project_status',
        'focus_groups',
        ['project_id', 'status'],
        postgresql_using='btree',
        postgresql_where=sa.text('deleted_at IS NULL')  # Ignoruj usunięte grupy
    )

    # Single index: deleted_at (używane w cleanup tasks)
    # Używane w: maintenance/cleanup_service.py
    # Przykład: DELETE FROM focus_groups WHERE deleted_at < NOW() - INTERVAL '7 days'
    op.create_index(
        'idx_focus_groups_deleted_at',
        'focus_groups',
        ['deleted_at'],
        postgresql_using='btree',
        postgresql_where=sa.text('deleted_at IS NOT NULL')  # Partial index
    )


def downgrade():
    """Usuwa performance indexes."""

    # FocusGroups indexes
    op.drop_index('idx_focus_groups_deleted_at', table_name='focus_groups')
    op.drop_index('idx_focus_groups_project_status', table_name='focus_groups')
    op.drop_index('idx_focus_groups_project_deleted', table_name='focus_groups')

    # Projects indexes
    op.drop_index('idx_projects_deleted_at', table_name='projects')
    op.drop_index('idx_projects_owner_deleted', table_name='projects')

    # Personas indexes
    op.drop_index('idx_personas_deleted_at', table_name='personas')
    op.drop_index('idx_personas_project_active', table_name='personas')
    op.drop_index('idx_personas_project_deleted', table_name='personas')
