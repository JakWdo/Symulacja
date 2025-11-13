#!/usr/bin/env python3
"""
Backfill Script - Shared Context Data Migration

Migruje istniejące dane do nowego modelu Shared Context (Faza 2).

Operacje:
1. Utworzenie "Default Environment" dla każdego teamu
2. Przypięcie istniejących projektów do domyślnego środowiska teamu
3. Przypięcie istniejących person do domyślnego środowiska projektu/teamu
4. Przypięcie istniejących workflows do domyślnego środowiska projektu/teamu

Użycie:
    python scripts/backfill_shared_context.py

Uwaga:
    - Skrypt jest idempotentny (może być uruchomiony wielokrotnie)
    - Nie nadpisuje istniejących environment_id (jeśli już ustawione)
    - Tworzy domyślne środowisko tylko jeśli nie istnieje
"""

import asyncio
import logging
import sys
from pathlib import Path

# Dodaj root projektu do PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Team, Environment, Project, Persona, Workflow
from config import app as app_config

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# === Database Session ===

# Utwórz async engine
engine = create_async_engine(
    app_config.database_url,
    echo=False,
    future=True,
)

# Utwórz async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_or_create_default_environment(db: AsyncSession, team_id) -> Environment:
    """
    Pobiera lub tworzy domyślne środowisko dla teamu.

    Args:
        db: Database session
        team_id: UUID teamu

    Returns:
        Environment instance (istniejące lub nowo utworzone)
    """
    # Sprawdź czy już istnieje domyślne środowisko
    result = await db.execute(
        select(Environment).where(
            and_(
                Environment.team_id == team_id,
                Environment.name == "Default Environment",
                Environment.is_active == True,
            )
        )
    )
    environment = result.scalar_one_or_none()

    if environment:
        logger.info(f"  ✓ Default environment już istnieje dla team {team_id}")
        return environment

    # Utwórz nowe domyślne środowisko
    environment = Environment(
        team_id=team_id,
        name="Default Environment",
        description="Automatically created default environment for team resources",
        is_active=True,
    )
    db.add(environment)
    await db.flush()  # Flush aby uzyskać ID

    logger.info(f"  ✓ Utworzono default environment dla team {team_id}")
    return environment


async def backfill_projects(db: AsyncSession) -> dict:
    """
    Backfill environment_id dla istniejących projektów.

    Returns:
        Dict ze statystykami: {updated: int, skipped: int, errors: int}
    """
    logger.info("Backfilling projects...")
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    # Pobierz projekty bez environment_id
    result = await db.execute(
        select(Project).where(
            and_(
                Project.environment_id.is_(None),
                Project.team_id.isnot(None),  # Musi mieć team_id
            )
        )
    )
    projects = result.scalars().all()

    logger.info(f"Znaleziono {len(projects)} projektów bez environment_id")

    for project in projects:
        try:
            # Pobierz lub utwórz domyślne środowisko dla teamu projektu
            environment = await get_or_create_default_environment(db, project.team_id)

            # Ustaw environment_id
            project.environment_id = environment.id
            stats["updated"] += 1

        except Exception as e:
            logger.error(f"Błąd podczas backfill projektu {project.id}: {e}")
            stats["errors"] += 1

    # Policz pominięte (już miały environment_id)
    result_total = await db.execute(select(Project))
    total_projects = len(result_total.scalars().all())
    stats["skipped"] = total_projects - len(projects)

    logger.info(f"Projects backfill: {stats['updated']} updated, {stats['skipped']} skipped, {stats['errors']} errors")
    return stats


async def backfill_personas(db: AsyncSession) -> dict:
    """
    Backfill environment_id dla istniejących person.

    Returns:
        Dict ze statystykami: {updated: int, skipped: int, errors: int}
    """
    logger.info("Backfilling personas...")
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    # Pobierz persony bez environment_id (ale z projektem i teamem)
    result = await db.execute(
        select(Persona)
        .join(Project, Persona.project_id == Project.id)
        .where(
            and_(
                Persona.environment_id.is_(None),
                Project.team_id.isnot(None),
            )
        )
    )
    personas = result.scalars().all()

    logger.info(f"Znaleziono {len(personas)} person bez environment_id")

    for persona in personas:
        try:
            # Pobierz projekt
            project_result = await db.execute(
                select(Project).where(Project.id == persona.project_id)
            )
            project = project_result.scalar_one()

            if not project.team_id:
                logger.warning(f"Persona {persona.id} ma projekt bez team_id - pomijam")
                stats["skipped"] += 1
                continue

            # Pobierz lub utwórz domyślne środowisko dla teamu
            environment = await get_or_create_default_environment(db, project.team_id)

            # Ustaw environment_id
            persona.environment_id = environment.id
            stats["updated"] += 1

        except Exception as e:
            logger.error(f"Błąd podczas backfill persony {persona.id}: {e}")
            stats["errors"] += 1

    # Policz pominięte (już miały environment_id)
    result_total = await db.execute(select(Persona))
    total_personas = len(result_total.scalars().all())
    stats["skipped"] += total_personas - len(personas)

    logger.info(f"Personas backfill: {stats['updated']} updated, {stats['skipped']} skipped, {stats['errors']} errors")
    return stats


async def backfill_workflows(db: AsyncSession) -> dict:
    """
    Backfill environment_id dla istniejących workflows.

    Returns:
        Dict ze statystykami: {updated: int, skipped: int, errors: int}
    """
    logger.info("Backfilling workflows...")
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    # Pobierz workflows bez environment_id (ale z projektem i teamem)
    result = await db.execute(
        select(Workflow)
        .join(Project, Workflow.project_id == Project.id)
        .where(
            and_(
                Workflow.environment_id.is_(None),
                Project.team_id.isnot(None),
            )
        )
    )
    workflows = result.scalars().all()

    logger.info(f"Znaleziono {len(workflows)} workflows bez environment_id")

    for workflow in workflows:
        try:
            # Pobierz projekt
            project_result = await db.execute(
                select(Project).where(Project.id == workflow.project_id)
            )
            project = project_result.scalar_one()

            if not project.team_id:
                logger.warning(f"Workflow {workflow.id} ma projekt bez team_id - pomijam")
                stats["skipped"] += 1
                continue

            # Pobierz lub utwórz domyślne środowisko dla teamu
            environment = await get_or_create_default_environment(db, project.team_id)

            # Ustaw environment_id
            workflow.environment_id = environment.id
            stats["updated"] += 1

        except Exception as e:
            logger.error(f"Błąd podczas backfill workflow {workflow.id}: {e}")
            stats["errors"] += 1

    # Policz pominięte (już miały environment_id)
    result_total = await db.execute(select(Workflow))
    total_workflows = len(result_total.scalars().all())
    stats["skipped"] += total_workflows - len(workflows)

    logger.info(f"Workflows backfill: {stats['updated']} updated, {stats['skipped']} skipped, {stats['errors']} errors")
    return stats


async def main():
    """Główna funkcja backfill."""
    logger.info("=" * 60)
    logger.info("Shared Context Data Migration - Backfill Script")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # 1. Backfill projects
            project_stats = await backfill_projects(db)

            # 2. Backfill personas
            persona_stats = await backfill_personas(db)

            # 3. Backfill workflows
            workflow_stats = await backfill_workflows(db)

            # Commit wszystkich zmian
            await db.commit()

            # Podsumowanie
            logger.info("=" * 60)
            logger.info("Backfill zakończony pomyślnie!")
            logger.info("=" * 60)
            logger.info(f"Projects:  {project_stats['updated']} updated, {project_stats['skipped']} skipped, {project_stats['errors']} errors")
            logger.info(f"Personas:  {persona_stats['updated']} updated, {persona_stats['skipped']} skipped, {persona_stats['errors']} errors")
            logger.info(f"Workflows: {workflow_stats['updated']} updated, {workflow_stats['skipped']} skipped, {workflow_stats['errors']} errors")
            logger.info("=" * 60)

            total_updated = project_stats['updated'] + persona_stats['updated'] + workflow_stats['updated']
            total_errors = project_stats['errors'] + persona_stats['errors'] + workflow_stats['errors']

            if total_errors > 0:
                logger.warning(f"⚠️  Backfill zakończony z {total_errors} błędami")
                sys.exit(1)
            else:
                logger.info(f"✅ Wszystkie {total_updated} rekordów zaktualizowane pomyślnie")
                sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Krytyczny błąd podczas backfill: {e}")
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
