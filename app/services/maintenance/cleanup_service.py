"""
Cleanup Service - Permanent Deletion Job

Usuwa (hard delete) soft-deleted entities które przekroczyły restore window (7 dni).
Uruchamiany codziennie przez APScheduler o 2:00 AM UTC.

Usuwa:
- Projects (deleted_at > 7 days ago)
- Personas (deleted_at > 7 days ago)
- Focus Groups (deleted_at > 7 days ago)
- Surveys (deleted_at > 7 days ago)

CASCADE behavior:
Database CASCADE DELETE automatycznie usuwa powiązane entities:
- Usunięcie Project → usuwa Personas, FocusGroups, Surveys (CASCADE)
- Usunięcie Persona → usuwa PersonaResponse, PersonaEvent, PersonaAuditLog (CASCADE)
- Usunięcie FocusGroup → usuwa PersonaResponse (CASCADE)
- Usunięcie Survey → usuwa SurveyResponse (CASCADE)
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Persona, FocusGroup, Survey

logger = logging.getLogger(__name__)


class CleanupService:
    """Service dla permanent deletion starych soft-deleted entities"""

    def __init__(self, retention_days: int = 7):
        """
        Initialize CleanupService

        Args:
            retention_days: Liczba dni retention window (default: 7)
                Po tym czasie soft-deleted entities są permanentnie usuwane
        """
        self.retention_days = retention_days

    async def cleanup_old_deleted_entities(self, db: AsyncSession) -> dict[str, int]:
        """
        Usuń (hard delete) wszystkie soft-deleted entities starsze niż retention_days

        Ten proces jest **nieodwracalny**. Entities są usuwane z bazy danych
        wraz z wszystkimi powiązanymi danymi (CASCADE).

        Args:
            db: AsyncSession do bazy danych

        Returns:
            dict[str, int]: Statystyki usuniętych entities
                {
                    "projects_deleted": 5,
                    "personas_deleted": 45,
                    "focus_groups_deleted": 12,
                    "surveys_deleted": 3,
                    "total_deleted": 65
                }

        Flow:
            1. Calculate cutoff date (now - retention_days)
            2. Hard DELETE projects where deleted_at < cutoff (CASCADE usuwa personas/focus_groups/surveys)
            3. Hard DELETE orphaned personas gdzie deleted_at < cutoff
            4. Hard DELETE orphaned focus_groups gdzie deleted_at < cutoff
            5. Hard DELETE orphaned surveys gdzie deleted_at < cutoff
            6. Commit transaction
            7. Return statistics

        Database CASCADE behavior:
            - DELETE Project → auto-deletes Personas, FocusGroups, Surveys (ondelete='CASCADE')
            - DELETE Persona → auto-deletes PersonaResponse, PersonaEvent, PersonaAuditLog
            - DELETE FocusGroup → auto-deletes PersonaResponse
            - DELETE Survey → auto-deletes SurveyResponse
        """
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        logger.info(
            f"🗑️  Starting cleanup job: deleting entities older than {cutoff_date.isoformat()}"
        )

        # Statystyki
        stats = {
            "projects_deleted": 0,
            "personas_deleted": 0,
            "focus_groups_deleted": 0,
            "surveys_deleted": 0,
            "total_deleted": 0,
        }

        try:
            # 1. Hard DELETE projects (CASCADE usuwa personas, focus_groups, surveys)
            projects_result = await db.execute(
                delete(Project)
                .where(Project.deleted_at.isnot(None))
                .where(Project.deleted_at < cutoff_date)
            )
            stats["projects_deleted"] = projects_result.rowcount

            # 2. Hard DELETE orphaned personas (które nie zostały usunięte przez project CASCADE)
            # Np. persony usunięte pojedynczo, nie przez project delete
            personas_result = await db.execute(
                delete(Persona)
                .where(Persona.deleted_at.isnot(None))
                .where(Persona.deleted_at < cutoff_date)
            )
            stats["personas_deleted"] = personas_result.rowcount

            # 3. Hard DELETE orphaned focus groups
            focus_groups_result = await db.execute(
                delete(FocusGroup)
                .where(FocusGroup.deleted_at.isnot(None))
                .where(FocusGroup.deleted_at < cutoff_date)
            )
            stats["focus_groups_deleted"] = focus_groups_result.rowcount

            # 4. Hard DELETE orphaned surveys
            surveys_result = await db.execute(
                delete(Survey)
                .where(Survey.deleted_at.isnot(None))
                .where(Survey.deleted_at < cutoff_date)
            )
            stats["surveys_deleted"] = surveys_result.rowcount

            # Commit wszystkich zmian
            await db.commit()

            # Calculate total
            stats["total_deleted"] = (
                stats["projects_deleted"]
                + stats["personas_deleted"]
                + stats["focus_groups_deleted"]
                + stats["surveys_deleted"]
            )

            logger.info(
                f"✅ Cleanup job completed successfully: {stats['total_deleted']} entities deleted "
                f"(projects: {stats['projects_deleted']}, personas: {stats['personas_deleted']}, "
                f"focus_groups: {stats['focus_groups_deleted']}, surveys: {stats['surveys_deleted']})"
            )

            return stats

        except Exception as e:
            logger.error(f"❌ Cleanup job failed: {str(e)}", exc_info=True)
            await db.rollback()
            raise

    async def cleanup_projects(self, db: AsyncSession) -> int:
        """
        Usuń tylko stare projekty (helper function)

        Args:
            db: AsyncSession

        Returns:
            int: Liczba usuniętych projektów
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        result = await db.execute(
            delete(Project)
            .where(Project.deleted_at.isnot(None))
            .where(Project.deleted_at < cutoff_date)
        )

        await db.commit()
        return result.rowcount

    async def cleanup_personas(self, db: AsyncSession) -> int:
        """
        Usuń tylko stare persony (helper function)

        Args:
            db: AsyncSession

        Returns:
            int: Liczba usuniętych person
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        result = await db.execute(
            delete(Persona)
            .where(Persona.deleted_at.isnot(None))
            .where(Persona.deleted_at < cutoff_date)
        )

        await db.commit()
        return result.rowcount
