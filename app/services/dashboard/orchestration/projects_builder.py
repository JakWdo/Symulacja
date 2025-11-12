"""Projects Builder - Lista aktywnych projektów z health status i progress.

Moduł odpowiada za:
- Pobieranie aktywnych projektów użytkownika
- Ocena health status per project
- Tracking progress stages (demographics → personas → focus → analysis)
- Generowanie CTA (Call-to-Action) buttons
- Optymalizacja N+1 queries (GROUP BY dla insights counts)
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import InsightEvidence, Project
from app.services.dashboard.metrics import ProjectHealthService

logger = logging.getLogger(__name__)


async def get_active_projects(
    db: AsyncSession,
    user_id: UUID,
    health_service: ProjectHealthService,
) -> list[dict[str, Any]]:
    """Pobierz active projects z health status, progress, insights count.

    Returns:
        Lista projektów z:
        - health: {status, score, color}
        - progress: {demographics, personas, focus, analysis, current_stage}
        - insights_count, new_insights_count
        - cta_label, cta_url
    """
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
            selectinload(Project.personas),
            selectinload(Project.focus_groups),
        )
        .order_by(Project.updated_at.desc())
        .limit(10)
    )

    result = await db.execute(stmt)
    projects = list(result.scalars().all())

    # Optimize N+1: Get all insights counts in one query with GROUP BY
    project_ids = [p.id for p in projects]

    # Total insights per project
    insights_counts_stmt = (
        select(
            InsightEvidence.project_id,
            func.count(InsightEvidence.id).label("count")
        )
        .where(InsightEvidence.project_id.in_(project_ids))
        .group_by(InsightEvidence.project_id)
    )
    insights_counts_result = await db.execute(insights_counts_stmt)
    insights_counts_map = {row.project_id: row.count for row in insights_counts_result}

    # New (unviewed) insights per project
    new_insights_counts_stmt = (
        select(
            InsightEvidence.project_id,
            func.count(InsightEvidence.id).label("count")
        )
        .where(
            and_(
                InsightEvidence.project_id.in_(project_ids),
                InsightEvidence.viewed_at.is_(None),
            )
        )
        .group_by(InsightEvidence.project_id)
    )
    new_insights_counts_result = await db.execute(new_insights_counts_stmt)
    new_insights_counts_map = {row.project_id: row.count for row in new_insights_counts_result}

    output = []
    for project in projects:
        # Get health
        health = await health_service.assess_project_health(project.id)

        # Progress stages (filter soft-deleted)
        has_demographics = bool(project.target_demographics)
        active_personas = [p for p in project.personas if p.deleted_at is None]
        active_focus_groups = [fg for fg in project.focus_groups if fg.deleted_at is None]
        has_personas = bool(active_personas and len(active_personas) > 0)
        has_focus = bool(active_focus_groups and len(active_focus_groups) > 0)

        # Get insights counts from pre-fetched maps (N+1 optimization)
        insights_count = insights_counts_map.get(project.id, 0)
        new_insights_count = new_insights_counts_map.get(project.id, 0)

        # Determine current stage
        if not has_personas:
            current_stage = "demographics"
        elif not has_focus:
            current_stage = "personas"
        elif insights_count == 0:
            current_stage = "focus"
        else:
            current_stage = "analysis"

        # Determine status (use active_focus_groups filtered above)
        if health["health_status"] == "blocked":
            status = "blocked"
        elif any(fg.status == "in_progress" for fg in active_focus_groups):
            status = "running"
        elif active_focus_groups and all(fg.status == "completed" for fg in active_focus_groups):
            status = "completed"
        else:
            status = "paused"

        # CTA (Call-to-Action)
        if health["health_status"] == "blocked":
            cta_label = "Fix Issues"
            cta_url = f"/projects/{project.id}"
        elif not has_personas:
            cta_label = "Generate Personas"
            cta_url = f"/projects/{project.id}/personas/generate"
        elif not has_focus:
            cta_label = "Start Focus Group"
            cta_url = f"/projects/{project.id}/focus-groups/create"
        elif new_insights_count > 0:
            cta_label = "View Insights"
            cta_url = f"/projects/{project.id}/insights"
        else:
            cta_label = "View Project"
            cta_url = f"/projects/{project.id}"

        output.append(
            {
                "id": str(project.id),
                "name": project.name,
                "status": status,
                "health": {
                    "status": health["health_status"],
                    "score": health["health_score"],
                    "color": (
                        "green"
                        if health["health_status"] == "on_track"
                        else "yellow"
                        if health["health_status"] == "at_risk"
                        else "red"
                    ),
                },
                "progress": {
                    "demographics": has_demographics,
                    "personas": has_personas,
                    "focus": has_focus,
                    "analysis": insights_count > 0,
                    "current_stage": current_stage,
                },
                "insights_count": insights_count or 0,
                "new_insights_count": new_insights_count or 0,
                "last_activity": project.updated_at,
                "cta_label": cta_label,
                "cta_url": cta_url,
            }
        )

    return output
