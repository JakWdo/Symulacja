"""
Project Health Service - Ocena zdrowia projektów

Health scoring:
- on_track: Wszystko działa, brak blokerów (score >= 80)
- at_risk: Jeden lub więcej minor blockers (score 50-79)
- blocked: Critical blocker (score < 50)

Blockers:
- no_personas: Brak person w projekcie (CRITICAL)
- incomplete_focus: Focus group nie ukończony
- low_coverage: Persona coverage <60% (is_statistically_valid = False)
- low_confidence: Insights z confidence <0.5
- analysis_failed: Ostatnia analiza failed
- budget_exceeded: Budget >100%
- idle_focus: Focus group bezczynny >48h (MEDIUM)
- no_focus_groups: Brak grup fokusowych (MEDIUM)
- no_insights: Brak insightów mimo ukończonych focus groups (MEDIUM)
"""

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InsightEvidence, Project, ProjectHealthLog
from app.utils import get_utc_now


class ProjectHealthService:
    """
    Serwis do oceny zdrowia projektów badawczych

    Umożliwia:
    - Ocenę health status projektu (on_track/at_risk/blocked)
    - Detekcję blokerów (no personas, low coverage, idle focus groups, etc.)
    - Obliczanie health score (0-100)
    - Logowanie historii health status
    - Pobieranie historii zmian health
    """

    def __init__(self, db: AsyncSession):
        """
        Inicjalizuj serwis

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def assess_project_health(self, project_id: UUID) -> dict[str, Any]:
        """
        Oceń health projektu i zwróć status + blockers

        Args:
            project_id: UUID projektu

        Returns:
            {
                "health_status": "on_track" | "at_risk" | "blocked",
                "health_score": int (0-100),
                "blockers": [
                    {
                        "type": "no_personas",
                        "severity": "critical" | "high" | "medium" | "low",
                        "message": "No personas generated yet",
                        "fix_action": "generate_personas",
                    },
                    ...
                ],
            }
        """
        blockers = await self._detect_blockers(project_id)

        # Calculate health score based on blockers
        health_score = 100
        for blocker in blockers:
            if blocker["severity"] == "critical":
                health_score -= 40
            elif blocker["severity"] == "high":
                health_score -= 20
            elif blocker["severity"] == "medium":
                health_score -= 10
            else:
                health_score -= 5

        health_score = max(0, health_score)

        # Determine status
        if health_score >= 80:
            health_status = "on_track"
        elif health_score >= 50:
            health_status = "at_risk"
        else:
            health_status = "blocked"

        return {
            "health_status": health_status,
            "health_score": health_score,
            "blockers": blockers,
        }

    async def _detect_blockers(self, project_id: UUID) -> list[dict[str, Any]]:
        """
        Wykryj wszystkie blokery dla projektu

        Args:
            project_id: UUID projektu

        Returns:
            Lista blokerów z type, severity, message, fix_action
        """
        blockers = []

        # Load project with relations
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.personas),
                selectinload(Project.focus_groups),
            )
        )
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            return blockers

        # Filter soft-deleted entities
        active_personas = [p for p in project.personas if p.deleted_at is None]
        active_focus_groups = [fg for fg in project.focus_groups if fg.deleted_at is None]

        # Blocker 1: No personas (CRITICAL)
        if not active_personas or len(active_personas) == 0:
            blockers.append(
                {
                    "type": "no_personas",
                    "severity": "critical",
                    "message": "No personas generated yet. Start by generating personas to match your target demographics.",
                    "fix_action": "generate_personas",
                }
            )

        # Blocker 2: Low coverage (HIGH)
        if not project.is_statistically_valid:
            blockers.append(
                {
                    "type": "low_coverage",
                    "severity": "high",
                    "message": "Persona coverage below target. Generate more personas to match demographic distribution.",
                    "fix_action": "generate_more_personas",
                }
            )

        # Blocker 3: No focus groups (MEDIUM) - tylko jeśli ma persony
        if active_personas and len(active_personas) > 0:
            if not active_focus_groups or len(active_focus_groups) == 0:
                blockers.append(
                    {
                        "type": "no_focus_groups",
                        "severity": "medium",
                        "message": "No focus groups created. Start a focus group discussion to gather insights.",
                        "fix_action": "create_focus_group",
                    }
                )

        # Blocker 4: Incomplete/idle focus groups (MEDIUM)
        for fg in active_focus_groups:
            if fg.status == "in_progress":
                # Check if idle >48h (use max of all activity timestamps)
                last_activity = max(
                    fg.created_at,
                    fg.started_at or fg.created_at,
                    fg.completed_at or fg.created_at,
                    fg.updated_at or fg.created_at,
                )
                idle_hours = (get_utc_now() - last_activity).total_seconds() / 3600
                if idle_hours > 48:
                    blockers.append(
                        {
                            "type": "idle_focus_group",
                            "severity": "medium",
                            "message": f"Focus group '{fg.name}' idle for {int(idle_hours)}h. Resume or complete the discussion.",
                            "fix_action": "resume_focus_group",
                            "focus_group_id": str(fg.id),
                        }
                    )

        # Blocker 5: No insights (MEDIUM) - tylko jeśli ma completed focus groups
        if active_focus_groups:
            completed_fg = [fg for fg in active_focus_groups if fg.status == "completed"]
            if completed_fg:
                insights_count = await self.db.scalar(
                    select(func.count(InsightEvidence.id)).where(
                        InsightEvidence.project_id == project_id
                    )
                )
                if insights_count == 0:
                    blockers.append(
                        {
                            "type": "no_insights",
                            "severity": "medium",
                            "message": "No insights extracted yet. Analyze focus group discussions to discover patterns.",
                            "fix_action": "extract_insights",
                        }
                    )

        # Blocker 6: Low confidence insights (LOW)
        low_conf_count = await self.db.scalar(
            select(func.count(InsightEvidence.id)).where(
                and_(
                    InsightEvidence.project_id == project_id,
                    InsightEvidence.confidence_score < 0.5,
                )
            )
        )
        if low_conf_count and low_conf_count > 0:
            blockers.append(
                {
                    "type": "low_confidence_insights",
                    "severity": "low",
                    "message": f"{low_conf_count} insights have low confidence (<50%). Review and refine your discussion questions.",
                    "fix_action": "review_insights",
                }
            )

        return blockers

    async def log_health_status(self, project_id: UUID) -> ProjectHealthLog:
        """
        Oblicz i zapisz health status (background job)

        Args:
            project_id: UUID projektu

        Returns:
            ProjectHealthLog: Zapisany log
        """
        health = await self.assess_project_health(project_id)

        log = ProjectHealthLog(
            project_id=project_id,
            health_status=health["health_status"],
            health_score=health["health_score"],
            blockers=health["blockers"],
        )

        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        return log

    async def get_health_history(
        self, project_id: UUID, limit: int = 30
    ) -> list[ProjectHealthLog]:
        """
        Pobierz historię health status (ostatnie N dni)

        Args:
            project_id: UUID projektu
            limit: Liczba wpisów do pobrania (default 30)

        Returns:
            Lista ProjectHealthLog (sorted by checked_at DESC)
        """
        stmt = (
            select(ProjectHealthLog)
            .where(ProjectHealthLog.project_id == project_id)
            .order_by(ProjectHealthLog.checked_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_health(self, project_id: UUID) -> ProjectHealthLog | None:
        """
        Pobierz najnowszy health log dla projektu

        Args:
            project_id: UUID projektu

        Returns:
            ProjectHealthLog lub None jeśli brak logów
        """
        stmt = (
            select(ProjectHealthLog)
            .where(ProjectHealthLog.project_id == project_id)
            .order_by(ProjectHealthLog.checked_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_projects_by_health_status(
        self, user_id: UUID, status: str | None = None
    ) -> list[tuple[Project, ProjectHealthLog]]:
        """
        Pobierz projekty użytkownika z najnowszym health status

        Args:
            user_id: UUID użytkownika
            status: Filtruj po health_status ('on_track', 'at_risk', 'blocked', optional)

        Returns:
            Lista tupli (Project, ProjectHealthLog)
        """
        # Subquery: latest health log per project
        latest_health_subq = (
            select(
                ProjectHealthLog.project_id,
                func.max(ProjectHealthLog.checked_at).label("max_checked_at"),
            )
            .join(Project, ProjectHealthLog.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                    Project.is_active.is_(True),
                )
            )
            .group_by(ProjectHealthLog.project_id)
            .subquery()
        )

        # Main query: join with latest health logs
        stmt = (
            select(Project, ProjectHealthLog)
            .join(
                ProjectHealthLog,
                and_(
                    Project.id == ProjectHealthLog.project_id,
                    ProjectHealthLog.checked_at
                    == select(latest_health_subq.c.max_checked_at)
                    .where(latest_health_subq.c.project_id == Project.id)
                    .scalar_subquery(),
                ),
            )
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                    Project.is_active.is_(True),
                )
            )
        )

        if status:
            stmt = stmt.where(ProjectHealthLog.health_status == status)

        result = await self.db.execute(stmt)
        return list(result.all())
