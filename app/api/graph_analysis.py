"""
API endpointy dla analizy grafowej
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User
from app.api.dependencies import get_current_user, get_focus_group_for_user
from app.services.graph_service import GraphService
from app.schemas.graph import (
    GraphDataResponse,
    GraphStatsResponse,
    InfluentialPersonasResponse,
    KeyConceptsResponse,
    GraphQueryRequest,
    GraphQueryResponse
)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/build/{focus_group_id}", response_model=GraphStatsResponse)
async def build_graph(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        stats = await service.build_graph_from_focus_group(db, str(focus_group_id))
        return GraphStatsResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}", response_model=GraphDataResponse)
async def get_graph(
    focus_group_id: UUID,
    filter_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        data = await service.get_graph_data(str(focus_group_id), filter_type, db)
        return GraphDataResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/influential", response_model=InfluentialPersonasResponse)
async def get_influential_personas(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Znajduje najbardziej wpływowe persony w grafie

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista person posortowanych według wpływu (influence score)
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        personas = await service.get_influential_personas(str(focus_group_id), db)
        return InfluentialPersonasResponse(personas=personas)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()

@router.post("/{focus_group_id}/ask", response_model=GraphQueryResponse)
async def ask_graph_question(
    focus_group_id: UUID,
    payload: GraphQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Odpowiada na pytanie w języku naturalnym dotyczące grafu wiedzy

    **Args:**
    - focus_group_id: UUID grupy fokusowej
    - payload: Pytanie zadane przez użytkownika

    **Returns:**
    - answer: Tekstowa odpowiedź
    - insights: Lista kluczowych insightów wspierających odpowiedź
    - suggested_questions: Podpowiedzi kolejnych zapytań
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        result = await service.answer_question(str(focus_group_id), payload.question, db)
        return GraphQueryResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/concepts", response_model=KeyConceptsResponse)
async def get_key_concepts(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobiera najczęściej wspominane koncepcje

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista konceptów z częstotliwością i sentimentem
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        concepts = await service.get_key_concepts(str(focus_group_id), db)
        return KeyConceptsResponse(concepts=concepts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/controversial")
async def get_controversial_concepts(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Znajduje koncepcje polaryzujące - tematy wywołujące skrajne opinie

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista konceptów z wysokim rozrzutem sentymentu, wraz z listą zwolenników i krytyków
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        controversial = await service.get_controversial_concepts(str(focus_group_id), db)
        return {"controversial_concepts": controversial}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/correlations")
async def get_trait_correlations(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Znajduje korelacje między cechami demograficznymi a opiniami

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista konceptów z różnicami w postrzeganiu między grupami wiekowymi

    **Example:**
    - Młodsi ludzie (<30) są bardziej pozytywni wobec "Innovation" niż seniorzy
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        correlations = await service.get_trait_opinion_correlations(str(focus_group_id), db)
        return {"correlations": correlations}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()


@router.get("/{focus_group_id}/emotions")
async def get_emotion_distribution(
    focus_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobiera rozkład emocji w grupie fokusowej

    **Args:**
    - focus_group_id: UUID grupy fokusowej

    **Returns:**
    - Lista emocji z liczbą person je wyrażających i intensywnością
    """
    await get_focus_group_for_user(focus_group_id, current_user, db)
    service = GraphService()
    try:
        emotions = await service.get_emotion_distribution(str(focus_group_id), db)
        return {"emotions": emotions}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.close()
