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

from app.models import FocusGroup, InsightEvidence, Project
from app.services.dashboard.health_service import ProjectHealthService


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
                        "title": "Napraw zablokowany projekt",
                        "description": f"Projekt '{project.name}' ma {len(health['blockers'])} krytycznych problemów.",
                        "icon": "AlertTriangle",
                        "context": {
                            "project_id": str(project.id),
                            "project_name": project.name,
                            "blocker_count": len(health["blockers"]),
                            "blockers": health["blockers"],
                        },
                        "cta_label": "Napraw problemy",
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
                        "title": "Wygeneruj persony",
                        "description": f"Projekt '{project.name}' potrzebuje person. Wygeneruj {project.target_sample_size} person (30-60s).",
                        "icon": "Users",
                        "context": {
                            "project_id": str(project.id),
                            "project_name": project.name,
                            "target_count": project.target_sample_size,
                        },
                        "cta_label": "Wygeneruj persony",
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
                    "title": "Przejrzyj nowe spostrzeżenia",
                    "description": f"{unviewed_count} nowych spostrzeżeń gotowych w '{project.name}'. Przejrzyj i podejmij działanie.",
                    "icon": "Lightbulb",
                    "context": {
                        "project_id": str(project.id),
                        "project_name": project.name,
                        "insight_count": unviewed_count,
                    },
                    "cta_label": "Zobacz spostrzeżenia",
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
                    from datetime import datetime, timedelta
                    now = datetime.utcnow()
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
                            "title": "Rozpocznij dyskusję grupy fokusowej",
                            "description": f"Projekt '{project.name}' ma {len(active_personas)} gotowych person. Rozpocznij grupę fokusową (2-5 min).",
                            "icon": "MessageSquare",
                            "context": {
                                "project_id": str(project.id),
                                "project_name": project.name,
                                "persona_count": len(active_personas),
                            },
                            "cta_label": "Rozpocznij grupę fokusową",
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
                    "title": "Rozpocznij swoje pierwsze badanie",
                    "description": "Utwórz projekt, zdefiniuj grupę docelową i wygeneruj persony.",
                    "icon": "Plus",
                    "context": {},
                    "cta_label": "Utwórz projekt",
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
