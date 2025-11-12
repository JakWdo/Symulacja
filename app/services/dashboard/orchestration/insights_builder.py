"""Insights Builder - Latest insights, insight detail, health blockers.

Moduł odpowiada za:
- Pobieranie latest insights (highlights) per user
- Insight detail z evidence trail + provenance
- Health blockers summary (on_track, at_risk, blocked)
- Tracking viewed insights (mark as viewed when fetched)
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InsightEvidence, Project
from app.services.dashboard.metrics import ProjectHealthService
from app.services.dashboard.insights import InsightTraceabilityService
from app.utils import get_utc_now

logger = logging.getLogger(__name__)


async def get_latest_insights(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 10
) -> list[dict[str, Any]]:
    """Pobierz latest insights (highlights).

    Returns:
        Lista insight highlights z:
        - project_name, insight_type, insight_text
        - confidence_score, impact_score
        - time_ago, evidence_count
        - is_viewed, is_adopted
    """
    stmt = (
        select(InsightEvidence)
        .join(Project, InsightEvidence.project_id == Project.id)
        .where(
            and_(
                Project.owner_id == user_id,
                Project.deleted_at.is_(None),
            )
        )
        .order_by(InsightEvidence.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    insights = list(result.scalars().all())

    # Get project names (optimize N+1)
    project_ids = list(set(ins.project_id for ins in insights))
    projects_stmt = select(Project).where(Project.id.in_(project_ids))
    projects_result = await db.execute(projects_stmt)
    projects_map = {p.id: p for p in projects_result.scalars().all()}

    output = []
    for insight in insights:
        project = projects_map.get(insight.project_id)
        project_name = project.name if project else "Unknown"

        # Calculate time ago
        delta = get_utc_now() - insight.created_at
        if delta.days > 0:
            time_ago = f"{delta.days} days ago"
        elif delta.seconds > 3600:
            time_ago = f"{delta.seconds // 3600} hours ago"
        else:
            time_ago = f"{delta.seconds // 60} minutes ago"

        output.append(
            {
                "id": str(insight.id),
                "project_id": str(insight.project_id),
                "project_name": project_name,
                "insight_type": insight.insight_type,
                "insight_text": insight.insight_text,
                "confidence_score": insight.confidence_score,
                "impact_score": insight.impact_score,
                "time_ago": time_ago,
                "evidence_count": len(insight.evidence),
                "is_viewed": insight.viewed_at is not None,
                "is_adopted": insight.adopted_at is not None,
            }
        )

    return output


async def get_insight_detail(
    db: AsyncSession,
    insight_id: UUID,
    user_id: UUID,
    insight_service: InsightTraceabilityService,
) -> dict[str, Any]:
    """Pobierz insight detail z evidence trail + provenance.

    Args:
        insight_id: UUID insightu
        user_id: UUID użytkownika (security check)
        insight_service: InsightTraceabilityService (for tracking viewed)

    Returns:
        Insight detail z evidence, provenance, concepts, sentiment
    """
    stmt = (
        select(InsightEvidence)
        .join(Project, InsightEvidence.project_id == Project.id)
        .where(
            and_(
                InsightEvidence.id == insight_id,
                Project.owner_id == user_id,
            )
        )
    )

    result = await db.execute(stmt)
    insight = result.scalar_one()

    # Get project name
    project_stmt = select(Project).where(Project.id == insight.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one()

    # Calculate time ago
    delta = get_utc_now() - insight.created_at
    if delta.days > 0:
        time_ago = f"{delta.days} days ago"
    elif delta.seconds > 3600:
        time_ago = f"{delta.seconds // 3600} hours ago"
    else:
        time_ago = f"{delta.seconds // 60} minutes ago"

    # Mark as viewed (if not already)
    if not insight.viewed_at:
        await insight_service.track_insight_adoption(insight_id, "viewed")

    return {
        "id": str(insight.id),
        "project_id": str(insight.project_id),
        "project_name": project.name,
        "insight_type": insight.insight_type,
        "insight_text": insight.insight_text,
        "confidence_score": insight.confidence_score,
        "impact_score": insight.impact_score,
        "time_ago": time_ago,
        "evidence_count": len(insight.evidence),
        "is_viewed": insight.viewed_at is not None,
        "is_adopted": insight.adopted_at is not None,
        "evidence": insight.evidence,
        "concepts": insight.concepts,
        "sentiment": insight.sentiment,
        "provenance": {
            "model_version": insight.model_version,
            "prompt_hash": insight.prompt_hash,
            "sources": insight.sources,
            "created_at": insight.created_at,
        },
    }


async def get_health_blockers(
    db: AsyncSession,
    user_id: UUID,
    health_service: ProjectHealthService,
) -> dict[str, Any]:
    """Pobierz health summary + blockers list.

    Returns:
        {
            "summary": {"on_track": 5, "at_risk": 2, "blocked": 1},
            "blockers": [list of blockers with project context],
        }
    """
    projects_stmt = select(Project).where(
        and_(
            Project.owner_id == user_id,
            Project.is_active.is_(True),
            Project.deleted_at.is_(None),
        )
    )
    result = await db.execute(projects_stmt)
    projects = list(result.scalars().all())

    summary = {"on_track": 0, "at_risk": 0, "blocked": 0}
    all_blockers = []

    for project in projects:
        health = await health_service.assess_project_health(project.id)
        summary[health["health_status"]] += 1

        # Add blockers with project context
        for blocker in health["blockers"]:
            all_blockers.append(
                {
                    **blocker,
                    "project_id": str(project.id),
                    "project_name": project.name,
                }
            )

    return {"summary": summary, "blockers": all_blockers}
