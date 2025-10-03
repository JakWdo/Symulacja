from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from typing import List
from uuid import UUID

from app.db import AsyncSessionLocal, get_db
from app.models import FocusGroup, Project
from app.schemas.focus_group import (
    FocusGroupCreate,
    FocusGroupResponse,
    FocusGroupResultResponse,
)
from app.services import FocusGroupService

router = APIRouter()

# Keep track of running tasks to prevent garbage collection
_running_tasks = set()


@router.post("/projects/{project_id}/focus-groups", response_model=FocusGroupResponse, status_code=201)
async def create_focus_group(
    project_id: UUID,
    focus_group: FocusGroupCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new focus group"""

    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_focus_group = FocusGroup(
        project_id=project_id,
        name=focus_group.name,
        description=focus_group.description,
        persona_ids=focus_group.persona_ids,
        questions=focus_group.questions,
        mode=focus_group.mode,
    )

    db.add(db_focus_group)
    await db.commit()
    await db.refresh(db_focus_group)

    return db_focus_group


@router.post("/focus-groups/{focus_group_id}/run", status_code=202)
async def run_focus_group(
    focus_group_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Execute a focus group simulation"""
    import logging
    logger = logging.getLogger(__name__)

    # Verify focus group exists
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")

    if focus_group.status == "running":
        raise HTTPException(status_code=400, detail="Focus group is already running")

    # Schedule background task and keep reference
    logger.info(f"🎬 Scheduling focus group task: {focus_group_id}")
    task = asyncio.create_task(_run_focus_group_task(focus_group_id))

    # Keep task reference to prevent garbage collection
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    logger.info(f"📝 Task created and added to running tasks")

    return {
        "message": "Focus group execution started",
        "focus_group_id": str(focus_group_id),
    }


async def _run_focus_group_task(focus_group_id: UUID):
    """Background task to run focus group"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🎯 Background task started for focus group {focus_group_id}")

    try:
        async with AsyncSessionLocal() as db:
            service = FocusGroupService()
            logger.info(f"📦 Service created, calling run_focus_group...")
            result = await service.run_focus_group(db, str(focus_group_id))
            logger.info(f"✅ Focus group completed: {result.get('status')}")
    except Exception as e:
        logger.error(f"❌ Error in background task: {e}", exc_info=True)


@router.get("/focus-groups/{focus_group_id}", response_model=FocusGroupResultResponse)
async def get_focus_group(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get focus group results"""
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")

    return {
        "id": focus_group.id,
        "project_id": focus_group.project_id,
        "name": focus_group.name,
        "description": focus_group.description,
        "project_context": focus_group.project_context,
        "persona_ids": focus_group.persona_ids,
        "questions": focus_group.questions,
        "mode": focus_group.mode,
        "status": focus_group.status,
        "metrics": {
            "total_execution_time_ms": focus_group.total_execution_time_ms,
            "avg_response_time_ms": focus_group.avg_response_time_ms,
            "meets_requirements": focus_group.meets_performance_requirements(),
        },
        "created_at": focus_group.created_at,
        "started_at": focus_group.started_at,
        "completed_at": focus_group.completed_at,
    }


@router.get("/projects/{project_id}/focus-groups", response_model=List[FocusGroupResponse])
async def list_focus_groups(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List focus groups for a project"""
    result = await db.execute(
        select(FocusGroup)
        .where(FocusGroup.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    focus_groups = result.scalars().all()
    return focus_groups


@router.delete("/focus-groups/{focus_group_id}", status_code=204)
async def delete_focus_group(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a focus group (hard delete)"""
    result = await db.execute(
        select(FocusGroup).where(FocusGroup.id == focus_group_id)
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=404, detail="Focus group not found")

    await db.delete(focus_group)
    await db.commit()

    return None
