#!/usr/bin/env python3
"""
Skrypt backfill dla Teams - Migracja istniejących projektów do zespołów

Ten skrypt automatycznie:
1. Dla każdego użytkownika tworzy "Personal Team" (jeśli nie ma jeszcze żadnego teamu)
2. Dodaje użytkownika jako OWNER teamu
3. Przypina wszystkie jego projekty (bez team_id) do Personal Team

Użycie:
    python scripts/backfill_teams.py

Uwagi:
- Skrypt jest idempotentny - można uruchomić wielokrotnie bez skutków ubocznych
- Nie nadpisuje istniejących team_id w projektach
- Tworzy tylko jeden Personal Team per użytkownik (sprawdza czy już istnieje)
"""

import asyncio
import sys
import os
from pathlib import Path

# Dodaj katalog główny projektu do sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User, Project, Team, TeamMembership
from app.models.team import TeamRole
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def backfill_teams():
    """
    Główna funkcja backfill - tworzy Personal Teams dla użytkowników i przypina projekty.
    """
    # Pobierz DATABASE_URL z environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL nie jest ustawiony! Ustaw zmienną środowiskową przed uruchomieniem skryptu.")
        logger.info("Przykład: DATABASE_URL='postgresql+asyncpg://user:pass@localhost:5432/dbname' python scripts/backfill_teams.py")
        sys.exit(1)

    logger.info(f"🔌 Łączenie z bazą danych...")

    # Utwórz engine i session
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        try:
            # 1. Pobierz wszystkich użytkowników
            result = await session.execute(
                select(User).where(User.deleted_at.is_(None))
            )
            users = result.scalars().all()

            logger.info(f"📊 Znaleziono {len(users)} użytkowników do przetworzenia")

            teams_created = 0
            projects_assigned = 0

            for user in users:
                logger.info(f"\n👤 Przetwarzanie użytkownika: {user.email} (ID: {user.id})")

                # 2. Sprawdź czy użytkownik ma już jakiś team
                existing_team_count = await session.scalar(
                    select(func.count(TeamMembership.id)).where(
                        TeamMembership.user_id == user.id
                    )
                )

                if existing_team_count > 0:
                    logger.info(f"   ✓ Użytkownik już należy do {existing_team_count} teamów, pomijam tworzenie Personal Team")

                    # Ale nadal przypnij projekty bez team_id do pierwszego teamu użytkownika
                    first_team_result = await session.execute(
                        select(TeamMembership.team_id)
                        .where(TeamMembership.user_id == user.id)
                        .limit(1)
                    )
                    first_team_id = first_team_result.scalar_one_or_none()

                    if first_team_id:
                        # Przypnij projekty bez team_id do pierwszego teamu
                        orphan_projects = await session.execute(
                            select(Project).where(
                                Project.owner_id == user.id,
                                Project.team_id.is_(None),
                                Project.deleted_at.is_(None),
                            )
                        )
                        orphan_projects_list = orphan_projects.scalars().all()

                        if orphan_projects_list:
                            for project in orphan_projects_list:
                                project.team_id = first_team_id
                                projects_assigned += 1

                            logger.info(f"   📌 Przypięto {len(orphan_projects_list)} projektów do istniejącego teamu")

                    continue

                # 3. Utwórz Personal Team dla użytkownika
                personal_team = Team(
                    name=f"{user.full_name}'s Team",
                    description=f"Personal workspace for {user.email}",
                    is_active=True,
                )

                session.add(personal_team)
                await session.flush()  # Flush aby mieć ID teamu

                logger.info(f"   ✅ Utworzono Personal Team: {personal_team.name} (ID: {personal_team.id})")
                teams_created += 1

                # 4. Dodaj użytkownika jako OWNER teamu
                membership = TeamMembership(
                    team_id=personal_team.id,
                    user_id=user.id,
                    role_in_team=TeamRole.OWNER,
                )

                session.add(membership)
                logger.info(f"   👑 Dodano użytkownika jako OWNER teamu")

                # 5. Przypnij wszystkie projekty użytkownika do Personal Team
                # (tylko te bez team_id - nie nadpisujemy istniejących)
                projects_result = await session.execute(
                    select(Project).where(
                        Project.owner_id == user.id,
                        Project.team_id.is_(None),  # Tylko projekty bez teamu
                        Project.deleted_at.is_(None),
                    )
                )
                projects_to_assign = projects_result.scalars().all()

                if projects_to_assign:
                    for project in projects_to_assign:
                        project.team_id = personal_team.id
                        projects_assigned += 1

                    logger.info(f"   📌 Przypięto {len(projects_to_assign)} projektów do Personal Team")
                else:
                    logger.info(f"   ℹ️  Brak projektów do przypięcia (wszystkie już mają team_id)")

            # 6. Commit wszystkich zmian
            await session.commit()

            logger.info(f"\n✅ BACKFILL ZAKOŃCZONY POMYŚLNIE!")
            logger.info(f"   📊 Statystyki:")
            logger.info(f"      - Utworzono teamów: {teams_created}")
            logger.info(f"      - Przypisano projektów: {projects_assigned}")
            logger.info(f"      - Przetworzono użytkowników: {len(users)}")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ BŁĄD podczas backfill: {str(e)}")
            raise

        finally:
            await engine.dispose()


if __name__ == "__main__":
    logger.info("🚀 Rozpoczynanie backfill teams...")
    logger.info("⚠️  Ten skrypt utworzy Personal Teams dla wszystkich użytkowników")
    logger.info("⚠️  i przypnie ich projekty do tych teamów.\n")

    try:
        asyncio.run(backfill_teams())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Przerwano przez użytkownika")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ KRYTYCZNY BŁĄD: {str(e)}")
        sys.exit(1)
