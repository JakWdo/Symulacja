"""
API endpointy dla analizy grafowej
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.graph_service import GraphService
from app.schemas.graph import (
    GraphDataResponse,
    GraphStatsResponse,
    InfluentialPersonasResponse,
    KeyConceptsResponse
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/build/{focus_group_id}", response_model=GraphStatsResponse)
async def build_graph(
    focus_group_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Buduje graf wiedzy z danych focus group

    **Args:**
    - focus_group_id: UUID grupy fokusowej (musi być completed)

    **Returns:**
    - Statystyki: liczba dodanych nodes i relationships

    **Raises:**
    - 404: Focus group not found
    - 400: Focus group not completed
    """
    service = GraphService()
    try:
        stats = await service.build_graph_from_focus_group(db, focus_group_id)
        return GraphStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}", response_model=GraphDataResponse)
async def get_graph(
    focus_group_id: str,
    filter_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Pobiera dane grafu dla wizualizacji

    **Args:**
    - focus_group_id: UUID grupy fokusowej
    - filter_type: Opcjonalny filtr ('positive', 'negative', 'influence')

    **Returns:**
    - nodes: Lista nodes (personas, concepts, emotions)
    - links: Lista relationships między nodes

    **Example:**
    ```
    GET /api/v1/graph/{focus_group_id}?filter_type=positive
    ```
    """
    service = GraphService()
    try:
        data = await service.get_graph_data(focus_group_id, filter_type)
        return GraphDataResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/influential", response_model=InfluentialPersonasResponse)
async def get_influential_personas(
    focus_group_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Znajduje najbardziej wpływowe persony w grafie

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista person posortowanych według wpływu (influence score)
    """
    service = GraphService()
    try:
        personas = await service.get_influential_personas(focus_group_id)
        return InfluentialPersonasResponse(personas=personas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/concepts", response_model=KeyConceptsResponse)
async def get_key_concepts(
    focus_group_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Pobiera najczęściej wspominane koncepcje

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista konceptów z częstotliwością i sentimentem
    """
    service = GraphService()
    try:
        concepts = await service.get_key_concepts(focus_group_id)
        return KeyConceptsResponse(concepts=concepts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
