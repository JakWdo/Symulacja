"""
Persona API - Generation Endpoints

Główny moduł endpointów API do generowania person.
Zawiera router, limiter, helper functions i 2 endpointy HTTP (POST /generate, POST /generate/stream).
"""

import asyncio
import logging
import random
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.db import get_db
from app.models import User, GenerationProgress, GenerationStage
from app.api.dependencies import get_current_user, get_project_for_user
from app.schemas.persona import PersonaGenerateRequest
from config import features

# Import background task z validation_endpoints
from .validation_endpoints import _generate_personas_task, _running_tasks

# Import streaming helpers z orchestration_endpoints
from .orchestration_endpoints import _generate_personas_task_streaming


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


# ===== HELPER FUNCTIONS (used only in generation task) =====

def _infer_full_name(background_story: str | None) -> str | None:
    """
    Próbuje wyekstraktować pełne imię i nazwisko z background story.

    TODO: Implement proper name extraction logic.
    """
    if not background_story:
        return None

    # Simple regex pattern for Polish names (Imię Nazwisko)
    # This is a placeholder - should be replaced with proper NLP
    pattern = r'\b([A-ZŁŚĆŻŹ][a-złśćżźńęą]+)\s+([A-ZŁŚĆŻŹ][a-złśćżźńęą]+)\b'
    match = re.search(pattern, background_story)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None


def _fallback_full_name(gender: str | None, age: int) -> str:
    """
    Generates a fallback full name based on gender and age.

    TODO: Implement proper Polish name generator with age-appropriate names.
    """
    # Simple placeholder implementation
    if gender and gender.lower() in ["kobieta", "female"]:
        first_names = ["Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka"]
        last_names = ["Kowalska", "Nowak", "Wiśniewska", "Wójcik", "Kowalczyk"]
    else:
        first_names = ["Jan", "Piotr", "Krzysztof", "Andrzej", "Tomasz"]
        last_names = ["Kowalski", "Nowak", "Wiśniewski", "Wójcik", "Kowalczyk"]

    return f"{random.choice(first_names)} {random.choice(last_names)}"


def _extract_age_from_story(background_story: str | None) -> int | None:
    """
    Próbuje wyekstraktować wiek z background story.

    WAŻNE: Zwraca tylko wiek jeśli jest jawnie podany (np. "ma 35 lat").
    NIE ekstraktuje liczb z kontekstu "10 lat doświadczenia" → age=10 (to byłby bug!).

    TODO: Implement proper age extraction with context awareness.
    """
    if not background_story:
        return None

    # Pattern for explicit age mentions: "ma X lat", "jest w wieku X lat", "X-letni/a"
    patterns = [
        r'\bma\s+(\d{1,2})\s+lat',
        r'\bw\s+wieku\s+(\d{1,2})\s+lat',
        r'\b(\d{1,2})-letni',
        r'\b(\d{1,2})-letnia',
    ]

    for pattern in patterns:
        match = re.search(pattern, background_story, re.IGNORECASE)
        if match:
            age = int(match.group(1))
            # Sanity check: age should be between 18-100
            if 18 <= age <= 100:
                return age

    return None


def _get_consistent_occupation(
    education_level: str | None,
    income_bracket: str | None,
    age: int,
    personality: dict[str, Any],
    background_story: str,
) -> str:
    """
    Determines a consistent occupation based on education, income, age, and personality.

    TODO: Implement smart occupation matching logic based on Polish job market.
    """
    # Try to extract occupation from personality first
    occupation = personality.get("occupation")
    if occupation and isinstance(occupation, str) and occupation.strip():
        return occupation.strip()

    # Try to extract from background_story
    # Simple pattern matching (placeholder)
    occupation_patterns = [
        r'pracuje jako\s+([a-złśćżźńęą\s]+)',
        r'jest\s+([a-złśćżźńęą]+)em',
        r'zawód:\s+([a-złśćżźńęą\s]+)',
    ]

    for pattern in occupation_patterns:
        match = re.search(pattern, background_story, re.IGNORECASE)
        if match:
            occ = match.group(1).strip()
            if len(occ) > 3 and len(occ) < 50:
                return occ

    # Fallback based on education level
    if education_level:
        if "wyższe" in education_level.lower():
            occupations = ["Specjalista", "Menedżer", "Inżynier", "Konsultant"]
        elif "średnie" in education_level.lower():
            occupations = ["Technik", "Handlowiec", "Pracownik biurowy"]
        else:
            occupations = ["Pracownik fizyczny", "Sprzedawca", "Operator"]
        return random.choice(occupations)

    return "Pracownik"


def _fallback_polish_list(items: list[str] | None, defaults: list[str]) -> list[str]:
    """
    Returns items if valid, otherwise returns random sample from defaults.

    Args:
        items: List of items from LLM (may be None or empty)
        defaults: Default Polish values (e.g., demographics.poland.values)

    Returns:
        Valid list of items (3-5 items)
    """
    if items and isinstance(items, list) and len(items) > 0:
        # Filter out empty/invalid items
        valid_items = [item.strip() for item in items if isinstance(item, str) and item.strip()]
        if valid_items:
            return valid_items[:5]  # Max 5 items

    # Fallback to random sample from defaults
    if defaults and isinstance(defaults, list):
        sample_size = min(4, len(defaults))
        return random.sample(defaults, sample_size)

    return []


# ===== API ENDPOINTS =====

@router.post(
    "/projects/{project_id}/personas/generate",
    status_code=202,
    summary="Start persona generation job",
)
@limiter.limit("10/hour")  # Security: Limit expensive LLM operations
async def generate_personas(
    request: Request,  # Required by slowapi limiter
    project_id: UUID,
    generate_request: PersonaGenerateRequest,
    _background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),  # Potrzebne do weryfikacji projektu przed uruchomieniem zadania
    current_user: User = Depends(get_current_user),
):
    """
    Rozpocznij generowanie syntetycznych person dla projektu (w tle)

    Endpoint ten:
    1. Weryfikuje czy projekt istnieje
    2. Loguje request
    3. Uruchamia zadanie w tle przy użyciu asyncio.create_task (odpowiedź HTTP wraca od razu)
    4. Zwraca natychmiast potwierdzenie

    Faktyczne generowanie odbywa się asynchronicznie w _generate_personas_task().

    Args:
        project_id: UUID projektu
        request: Parametry generowania (num_personas, adversarial_mode, advanced_options)
        _background_tasks: FastAPI BackgroundTasks do uruchomienia zadania w tle (obecnie niewykorzystane)
        db: Sesja bazy (tylko do weryfikacji projektu)

    Returns:
        {
            "message": "Persona generation started in background",
            "project_id": str,
            "num_personas": int,
            "adversarial_mode": bool
        }

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
    """
    # Weryfikacja czy projekt istnieje (przed dodaniem do kolejki)
    await get_project_for_user(project_id, current_user, db)

    logger.info(
        "Persona generation request received",
        extra={
            "project_id": str(project_id),
            "num_personas": generate_request.num_personas,
            "adversarial_mode": generate_request.adversarial_mode,
        },
    )

    # Przygotuj advanced options (konwertuj None fields)
    advanced_payload = (
        generate_request.advanced_options.model_dump(exclude_none=True)
        if generate_request.advanced_options
        else None
    )

    # Utwórz zadanie asynchroniczne
    logger.info(f"Creating async task for persona generation (project={project_id}, personas={generate_request.num_personas}, use_rag={generate_request.use_rag})")
    task = asyncio.create_task(_generate_personas_task(
        project_id,
        generate_request.num_personas,
        generate_request.adversarial_mode,
        advanced_payload,
        generate_request.use_rag,
    ))

    # Zachowujemy referencję do zadania, aby GC go nie usunął
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    # Sprawdź czy orchestration jest włączone (dla warning w UI)
    orchestration_enabled = features.orchestration.enabled

    # Zwróć natychmiast (nie czekaj na zakończenie generowania)
    response = {
        "message": "Persona generation started in background",
        "project_id": str(project_id),
        "num_personas": generate_request.num_personas,
        "adversarial_mode": generate_request.adversarial_mode,
        "use_rag": generate_request.use_rag,
        "orchestration_enabled": orchestration_enabled,
    }

    # Dodaj warning jeśli orchestration wyłączone lub use_rag=false
    if not orchestration_enabled or not generate_request.use_rag:
        response["warning"] = (
            "Orchestration disabled - personas will not have detailed reasoning/briefs. "
            "Enable orchestration and use_rag for full persona insights."
        )

    return response


@router.post(
    "/projects/{project_id}/personas/generate/stream",
    summary="Stream persona generation progress (SSE)",
)
@limiter.limit("10/hour")  # Same rate limit as regular generation
async def generate_personas_stream(
    request: Request,  # Required by slowapi limiter
    project_id: UUID,
    generate_request: PersonaGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint dla real-time progress tracking generacji person.

    Ten endpoint zwraca Server-Sent Events stream z progress updates podczas
    generowania person. Każdy event zawiera:
    - stage: Aktualny etap (initializing, orchestration, generating_personas, etc.)
    - progress_percent: Postęp w procentach (0-100)
    - message: Czytelna wiadomość po polsku
    - personas_generated: Liczba wygenerowanych person
    - total_personas: Docelowa liczba person

    UWAGA: Cloud Run ma 60 min timeout dla requestów. Dla dużych generacji (100+ person)
    zalecany jest fallback do polling `/projects/{project_id}/personas`.

    Args:
        project_id: UUID projektu
        generate_request: Parametry generowania (num_personas, use_rag, etc.)
        db: Sesja bazy (tylko do weryfikacji projektu)
        current_user: Zalogowany użytkownik

    Returns:
        EventSourceResponse: SSE stream z progress events

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje
        HTTPException 500: Jeśli generacja failuje
    """
    # Weryfikacja czy projekt istnieje
    await get_project_for_user(project_id, current_user, db)

    logger.info(
        "SSE persona generation stream started",
        extra={
            "project_id": str(project_id),
            "num_personas": generate_request.num_personas,
            "use_rag": generate_request.use_rag,
        },
    )

    async def event_generator():
        """Generator dla SSE events - yield progress updates."""
        try:
            # Yield initial event
            yield {
                "event": "progress",
                "data": GenerationProgress(
                    stage=GenerationStage.INITIALIZING,
                    progress_percent=0,
                    message="Inicjalizacja generacji person...",
                    total_personas=generate_request.num_personas,
                    personas_generated=0,
                ).model_dump_json()
            }

            # Delegate to streaming task (nowa wersja _generate_personas_task)
            async for progress in _generate_personas_task_streaming(
                project_id=project_id,
                num_personas=generate_request.num_personas,
                adversarial_mode=generate_request.adversarial_mode,
                advanced_options=(
                    generate_request.advanced_options.model_dump(exclude_none=True)
                    if generate_request.advanced_options
                    else None
                ),
                use_rag=generate_request.use_rag,
            ):
                # Yield progress event
                yield {
                    "event": "progress",
                    "data": progress.model_dump_json()
                }

                # Zakończ stream jeśli completed lub failed
                if progress.stage in [GenerationStage.COMPLETED, GenerationStage.FAILED]:
                    break

            logger.info(
                "SSE persona generation stream completed",
                extra={"project_id": str(project_id)}
            )

        except Exception as e:
            logger.error(
                "SSE persona generation stream FAILED",
                exc_info=True,
                extra={
                    "project_id": str(project_id),
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:500],
                }
            )

            # Yield error event
            yield {
                "event": "progress",
                "data": GenerationProgress(
                    stage=GenerationStage.FAILED,
                    progress_percent=0,
                    message=f"Błąd generacji: {str(e)[:200]}",
                    total_personas=generate_request.num_personas,
                    personas_generated=0,
                    error=str(e)[:500],
                ).model_dump_json()
            }

    return EventSourceResponse(event_generator())
