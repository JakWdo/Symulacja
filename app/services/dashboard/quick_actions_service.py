"""
Quick Actions Service - Next Best Action Engine

Priorytetyzacja akcji:
1. Fix Issues (critical blockers)
2. Generate Personas (no personas)
3. Start/Resume Focus Group (personas ready, no active focus)
4. View Insights (insights ready)
5. Start New Research (all good, suggest new project)
"""

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InsightEvidence, Project, User
from app.services.dashboard.health_service import ProjectHealthService
from app.utils import get_utc_now


# Translation dictionaries for Quick Actions
TRANSLATIONS = {
    "pl": {
        "fix_blocker_title": "Napraw zablokowany projekt",
        "fix_blocker_desc": "Projekt '{project_name}' ma {blocker_count} krytycznych problemów.",
        "fix_blocker_cta": "Napraw problemy",
        "generate_personas_title": "Wygeneruj persony",
        "generate_personas_desc": "Projekt '{project_name}' potrzebuje person. Wygeneruj {target_count} person (30-60s).",
        "generate_personas_cta": "Wygeneruj persony",
        "view_insights_title": "Przejrzyj nowe spostrzeżenia",
        "view_insights_desc": "{insight_count} nowych spostrzeżeń gotowych w '{project_name}'. Przejrzyj i podejmij działanie.",
        "view_insights_cta": "Zobacz spostrzeżenia",
        "start_focus_title": "Rozpocznij dyskusję grupy fokusowej",
        "start_focus_desc": "Projekt '{project_name}' ma {persona_count} gotowych person. Rozpocznij grupę fokusową (2-5 min).",
        "start_focus_cta": "Rozpocznij grupę fokusową",
        "first_project_title": "Rozpocznij swoje pierwsze badanie",
        "first_project_desc": "Utwórz projekt, zdefiniuj grupę docelową i wygeneruj persony.",
        "first_project_cta": "Utwórz projekt",
    },
    "en": {
        "fix_blocker_title": "Fix blocked project",
        "fix_blocker_desc": "Project '{project_name}' has {blocker_count} critical issues.",
        "fix_blocker_cta": "Fix issues",
        "generate_personas_title": "Generate personas",
        "generate_personas_desc": "Project '{project_name}' needs personas. Generate {target_count} personas (30-60s).",
        "generate_personas_cta": "Generate personas",
        "view_insights_title": "Review new insights",
        "view_insights_desc": "{insight_count} new insights ready in '{project_name}'. Review and take action.",
        "view_insights_cta": "View insights",
        "start_focus_title": "Start focus group discussion",
        "start_focus_desc": "Project '{project_name}' has {persona_count} personas ready. Start focus group (2-5 min).",
        "start_focus_cta": "Start focus group",
        "first_project_title": "Start your first research",
        "first_project_desc": "Create a project, define your target audience, and generate personas.",
        "first_project_cta": "Create project",
    },
}


class QuickActionsService:
    """
    Serwis do rekomendacji akcji użytkownika (Next Best Action)

    Analizuje stan projektów użytkownika i sugeruje najbardziej wartościowe akcje do wykonania.
    """

    def __init__(self, db: AsyncSession, health_service: ProjectHealthService):
        """
        Inicjalizuj serwis

        Args:
            db: Async SQLAlchemy session
            health_service: Serwis health do oceny projektów
        """
        self.db = db
        self.health_service = health_service

    async def _get_user_language(self, user_id: UUID) -> str:
        """
        Pobierz preferowany język użytkownika

        Args:
            user_id: UUID użytkownika

        Returns:
            Kod języka ('pl' lub 'en'), domyślnie 'pl'
        """
        stmt = select(User.preferred_language).where(User.id == user_id)
        result = await self.db.execute(stmt)
        lang = result.scalar_one_or_none()
        return lang if lang in ['pl', 'en'] else 'pl'

    def _translate(self, key: str, lang: str, **kwargs) -> str:
        """
        Przetłumacz tekst z użyciem słownika tłumaczeń

        Args:
            key: Klucz tłumaczenia
            lang: Kod języka ('pl' lub 'en')
            **kwargs: Parametry do formatowania (np. project_name, count)

        Returns:
            Przetłumaczony i sformatowany tekst
        """
        translations = TRANSLATIONS.get(lang, TRANSLATIONS['pl'])
        text = translations.get(key, key)
        return text.format(**kwargs)

    async def recommend_actions(
        self, user_id: UUID, limit: int = 4
    ) -> list[dict[str, Any]]:
        """
        Zwróć top N recommended actions dla użytkownika

        Args:
            user_id: UUID użytkownika
            limit: Maksymalna liczba akcji (default 4)

        Returns:
            Lista akcji z priorytetem, title, description, context, CTA
        """
        actions = []

        # Get user's preferred language
        lang = await self._get_user_language(user_id)

        # Load user's projects
        stmt = (
            select(Project)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.is_active.is_(True),
                    Project.deleted_at.is_(None),
                )
            )
            .options(
                selectinload(Project.personas), selectinload(Project.focus_groups)
            )
        )
        result = await self.db.execute(stmt)
        projects = list(result.scalars().all())

        # Priority 1: Fix Issues (blocked projects)
        for project in projects:
            health = await self.health_service.assess_project_health(project.id)
            if health["health_status"] == "blocked":
                actions.append(
                    {
                        "action_id": f"fix_project_{project.id}",
                        "action_type": "fix_blocker",
                        "priority": "high",
                        "title": self._translate("fix_blocker_title", lang),
                        "description": self._translate("fix_blocker_desc", lang, project_name=project.name, blocker_count=len(health['blockers'])),
                        "icon": "AlertTriangle",
                        "context": {
                            "project_id": str(project.id),
                            "project_name": project.name,
                            "blocker_count": len(health["blockers"]),
                            "blockers": health["blockers"],
                        },
                        "cta_label": self._translate("fix_blocker_cta", lang),
                        "cta_url": f"/projects/{project.id}",
                    }
                )

        # Priority 2: Generate Personas (no personas yet)
        for project in projects:
            if not project.personas or len(project.personas) == 0:
                actions.append(
                    {
                        "action_id": f"generate_personas_{project.id}",
                        "action_type": "generate_personas",
                        "priority": "high",
                        "title": self._translate("generate_personas_title", lang),
                        "description": self._translate("generate_personas_desc", lang, project_name=project.name, target_count=project.target_sample_size),
                        "icon": "Users",
                        "context": {
                            "project_id": str(project.id),
                            "project_name": project.name,
                            "target_count": project.target_sample_size,
                        },
                        "cta_label": self._translate("generate_personas_cta", lang),
                        "cta_url": f"/projects/{project.id}/personas/generate",
                    }
                )

        # Priority 3: View Insights (insights ready, not viewed) - HIGH PRIORITY
        insights_stmt = (
            select(InsightEvidence)
            .join(Project, InsightEvidence.project_id == Project.id)
            .where(
                and_(
                    Project.owner_id == user_id,
                    Project.deleted_at.is_(None),
                    InsightEvidence.viewed_at.is_(None),
                )
            )
            .limit(1)
        )
        result = await self.db.execute(insights_stmt)
        unviewed_insight = result.scalar_one_or_none()

        # Check if there are unviewed insights (used to suppress "Start Focus Group")
        has_unviewed_insights = unviewed_insight is not None

        if unviewed_insight:
            project_stmt = select(Project).where(
                Project.id == unviewed_insight.project_id
            )
            result = await self.db.execute(project_stmt)
            project = result.scalar_one()

            # Count total unviewed
            unviewed_count = await self.db.scalar(
                select(func.count(InsightEvidence.id))
                .join(Project, InsightEvidence.project_id == Project.id)
                .where(
                    and_(
                        Project.owner_id == user_id,
                        Project.deleted_at.is_(None),
                        InsightEvidence.viewed_at.is_(None),
                    )
                )
            )
            actions.append(
                {
                    "action_id": f"view_insights_{project.id}",
                    "action_type": "view_insights",
                    "priority": "high",  # Changed from "medium" to "high"
                    "title": self._translate("view_insights_title", lang),
                    "description": self._translate("view_insights_desc", lang, insight_count=unviewed_count, project_name=project.name),
                    "icon": "Lightbulb",
                    "context": {
                        "project_id": str(project.id),
                        "project_name": project.name,
                        "insight_count": unviewed_count,
                    },
                    "cta_label": self._translate("view_insights_cta", lang),
                    "cta_url": f"/projects/{project.id}/insights",
                }
            )

        # Priority 4: Start Focus Group (personas ready, no active focus, no unviewed insights)
        # Don't suggest starting a new FG if there are unviewed insights or recently completed FG
        for project in projects:
            if project.personas and len(project.personas) > 0:
                # Filter soft-deleted personas
                active_personas = [p for p in project.personas if p.deleted_at is None]
                active_focus_groups = [fg for fg in project.focus_groups if fg.deleted_at is None]

                if not active_personas:
                    continue

                # Check if there's an active (in_progress) focus group
                active_focus = [
                    fg for fg in active_focus_groups if fg.status == "in_progress"
                ]

                if active_focus:
                    continue  # Already has active focus group

                # Check if FG was recently completed (within 24h)
                recently_completed = False
                if active_focus_groups:
                    from datetime import timedelta
                    now = get_utc_now()
                    for fg in active_focus_groups:
                        if fg.status == "completed" and fg.completed_at:
                            time_since_completion = now - fg.completed_at
                            if time_since_completion < timedelta(hours=24):
                                recently_completed = True
                                break

                # Don't suggest if:
                # 1. There are unviewed insights (user should review first)
                # 2. FG was completed in last 24h (give time to review)
                if not has_unviewed_insights and not recently_completed:
                    actions.append(
                        {
                            "action_id": f"start_focus_{project.id}",
                            "action_type": "start_focus_group",
                            "priority": "medium",
                            "title": self._translate("start_focus_title", lang),
                            "description": self._translate("start_focus_desc", lang, project_name=project.name, persona_count=len(active_personas)),
                            "icon": "MessageSquare",
                            "context": {
                                "project_id": str(project.id),
                                "project_name": project.name,
                                "persona_count": len(active_personas),
                            },
                            "cta_label": self._translate("start_focus_cta", lang),
                            "cta_url": f"/projects/{project.id}/focus-groups/create",
                        }
                    )

        # Priority 5: Start New Research (no projects or all completed)
        if len(projects) == 0:
            actions.append(
                {
                    "action_id": "create_first_project",
                    "action_type": "create_project",
                    "priority": "high",
                    "title": self._translate("first_project_title", lang),
                    "description": self._translate("first_project_desc", lang),
                    "icon": "Plus",
                    "context": {},
                    "cta_label": self._translate("first_project_cta", lang),
                    "cta_url": "/projects/create",
                }
            )

        # Sort by priority, limit
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda a: priority_order[a["priority"]])

        return actions[:limit]

    async def execute_action(
        self, action_id: str, user_id: UUID
    ) -> dict[str, Any]:
        """
        Execute action (trigger orchestration)

        Args:
            action_id: ID akcji (format: "action_type_entity_id")
            user_id: UUID użytkownika

        Returns:
            {
                "status": "success" | "redirect" | "error",
                "message": "...",
                "redirect_url": "/projects/{id}",
            }
        """
        # Parse action_id (format: "action_type_project_id")
        parts = action_id.split("_", 2)
        action_type = parts[0] + "_" + parts[1] if len(parts) > 2 else parts[0]
        entity_id = parts[2] if len(parts) > 2 else None

        if action_type == "fix_project":
            # Redirect to project detail
            return {
                "status": "redirect",
                "message": "Opening project to fix issues...",
                "redirect_url": f"/projects/{entity_id}",
            }

        elif action_type == "generate_personas":
            # Trigger persona generation
            return {
                "status": "redirect",
                "message": "Opening persona generation wizard...",
                "redirect_url": f"/projects/{entity_id}/personas/generate",
            }

        elif action_type == "start_focus":
            # Trigger focus group builder
            return {
                "status": "redirect",
                "message": "Opening focus group builder...",
                "redirect_url": f"/projects/{entity_id}/focus-groups/create",
            }

        elif action_type == "view_insights":
            # Redirect to insights
            return {
                "status": "redirect",
                "message": "Opening insights...",
                "redirect_url": f"/projects/{entity_id}/insights",
            }

        elif action_type == "create_project":
            # Redirect to project creation
            return {
                "status": "redirect",
                "message": "Opening project creation...",
                "redirect_url": "/projects/create",
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action type: {action_type}",
            }
