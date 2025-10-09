"""
API Endpoints dla Grup Fokusowych

Ten moduł zawiera endpoints do zarządzania symulowanymi grupami fokusowymi:
- POST /projects/{id}/focus-groups - Utworzenie grupy fokusowej
- PUT /focus-groups/{id} - Aktualizacja grupy fokusowej (draft editing)
- POST /focus-groups/{id}/run - Uruchomienie symulacji (background task)
- GET /focus-groups - Lista grup
- GET /focus-groups/{id} - Szczegóły grupy
- GET /focus-groups/{id}/results - Wyniki dyskusji z metrykami

Grupy fokusowe działają asynchronicznie - tworzenie jest natychmiastowe,
but wykonanie symulacji (run) działa w tle i może trwać kilkadziesiąt sekund.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from typing import List
from uuid import UUID

from app.db import AsyncSessionLocal, get_db
from app.models import FocusGroup, User
from app.api.dependencies import (
    get_current_user,
    get_project_for_user,
    get_focus_group_for_user,
)
from app.schemas.focus_group import (
    FocusGroupCreate,
    FocusGroupResponse,
    FocusGroupResultResponse,
)
from app.services import FocusGroupService

router = APIRouter()

# Śledź uruchomione zadania aby zapobiec garbage collection
# (Python może usunąć Task z pamięci jeśli nie ma do niego referencji)
_running_tasks = set()


@router.post("/projects/{project_id}/focus-groups", response_model=FocusGroupResponse, status_code=201)
async def create_focus_group(
    project_id: UUID,
    focus_group: FocusGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new focus group"""

    await get_project_for_user(project_id, current_user, db)

    db_focus_group = FocusGroup(
        project_id=project_id,
        name=focus_group.name,
        description=focus_group.description,
        persona_ids=focus_group.persona_ids,
        questions=focus_group.questions,
        mode=focus_group.mode,
        target_participants=focus_group.target_participants,
    )

    db.add(db_focus_group)
    await db.commit()
    await db.refresh(db_focus_group)

    return db_focus_group


@router.put("/focus-groups/{focus_group_id}", response_model=FocusGroupResponse)
async def update_focus_group(
    focus_group_id: UUID,
    focus_group_update: FocusGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a focus group (for draft editing)"""

    focus_group = await get_focus_group_for_user(focus_group_id, current_user, db)

    # Aktualizacje są dozwolone tylko dla grup w statusie "pending"
    if focus_group.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Can only update pending focus groups"
        )

    # Uaktualnij pola przekazane w żądaniu
    focus_group.name = focus_group_update.name
    focus_group.description = focus_group_update.description
    focus_group.persona_ids = focus_group_update.persona_ids
    focus_group.questions = focus_group_update.questions
    focus_group.mode = focus_group_update.mode
    focus_group.target_participants = focus_group_update.target_participants

    await db.commit()
    await db.refresh(focus_group)

    return focus_group


@router.post("/focus-groups/{focus_group_id}/run", status_code=202)
async def run_focus_group(
    focus_group_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a focus group simulation"""
    import logging
    logger = logging.getLogger(__name__)

    focus_group = await get_focus_group_for_user(focus_group_id, current_user, db)

    if focus_group.status == "running":
        raise HTTPException(status_code=400, detail="Focus group is already running")

    # Sprawdź minimalne wymagania przed uruchomieniem symulacji
    if len(focus_group.persona_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Focus group must have at least 2 personas (currently has {len(focus_group.persona_ids)})"
        )

    if len(focus_group.questions) < 1:
        raise HTTPException(
            status_code=400,
            detail="Focus group must have at least 1 question"
        )

    # Rejestrujemy zadanie w tle i zachowujemy referencję
    logger.info(f"🎬 Scheduling focus group task: {focus_group_id}")
    task = asyncio.create_task(_run_focus_group_task(focus_group_id))

    # Zapewniamy, że garbage collector nie usunie zadania
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
    from app.services.graph_service import GraphService
    logger = logging.getLogger(__name__)

    logger.info(f"🎯 Background task started for focus group {focus_group_id}")

    try:
        async with AsyncSessionLocal() as db:
            service = FocusGroupService()
            logger.info(f"📦 Service created, calling run_focus_group...")
            result = await service.run_focus_group(db, str(focus_group_id))
            logger.info(f"✅ Focus group completed: {result.get('status')}")

    # Po zakończeniu można samoczynnie budować graf wiedzy
            if result.get('status') == 'completed':
                logger.info(f"🔨 Building knowledge graph for focus group {focus_group_id}...")
                graph_service = GraphService()
                try:
                    graph_stats = await graph_service.build_graph_from_focus_group(db, str(focus_group_id))
                    logger.info(f"✅ Knowledge graph built successfully: {graph_stats}")
                except Exception as graph_error:
                    logger.error(f"⚠️  Failed to build knowledge graph (non-critical): {graph_error}", exc_info=True)
                finally:
                    await graph_service.close()
    except Exception as e:
        logger.error(f"❌ Error in background task: {e}", exc_info=True)


@router.get("/focus-groups/{focus_group_id}", response_model=FocusGroupResultResponse)
async def get_focus_group(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get focus group results"""
    focus_group = await get_focus_group_for_user(focus_group_id, current_user, db)

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
    current_user: User = Depends(get_current_user),
):
    """List focus groups for a project"""
    await get_project_for_user(project_id, current_user, db)
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
    current_user: User = Depends(get_current_user),
):
    """Delete a focus group (hard delete)"""
    focus_group = await get_focus_group_for_user(focus_group_id, current_user, db)

    await db.delete(focus_group)
    await db.commit()

    return None
