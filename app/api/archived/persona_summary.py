"""
Archived personas summary endpoint.

The original endpoint `/projects/{project_id}/personas/summary` is no longer
used by the frontend but the implementation is preserved here so it can be
restored easily if the dashboard view returns.
"""

from typing import List
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_project_for_user
from app.models import Persona, User
from app.schemas.archived.persona_summary import (
    PersonasSummaryResponse,
    PersonasSummarySegment,
)


async def get_personas_summary(
    project_id: UUID,
    db: AsyncSession,
    current_user: User,
) -> PersonasSummaryResponse:
    """
    Archived implementation of the personas summary dashboard endpoint.

    Original route:
        GET /projects/{project_id}/personas/summary
    """

    await get_project_for_user(project_id, current_user, db)

    totals_stmt = select(
        func.count().label("total"),
        func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
        func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
    ).where(Persona.project_id == project_id)

    totals_row = await db.execute(totals_stmt)
    totals = totals_row.first()
    total_personas = int(totals.total or 0) if totals else 0
    active_personas = int(totals.active or 0) if totals else 0
    archived_personas = int(totals.archived or 0) if totals else 0

    segments_stmt = (
        select(
            Persona.segment_id,
            Persona.segment_name,
            func.sum(case((Persona.is_active.is_(True), 1), else_=0)).label("active"),
            func.sum(case((Persona.is_active.is_(False), 1), else_=0)).label("archived"),
        )
        .where(Persona.project_id == project_id)
        .group_by(Persona.segment_id, Persona.segment_name)
    )
    segments_result = await db.execute(segments_stmt)

    segment_rows = segments_result.all()
    segments: List[PersonasSummarySegment] = [
        PersonasSummarySegment(
            segment_id=row.segment_id,
            segment_name=row.segment_name,
            active_personas=int(row.active or 0),
            archived_personas=int(row.archived or 0),
        )
        for row in segment_rows
    ]

    return PersonasSummaryResponse(
        project_id=project_id,
        total_personas=total_personas,
        active_personas=active_personas,
        archived_personas=archived_personas,
        segments=segments,
    )
