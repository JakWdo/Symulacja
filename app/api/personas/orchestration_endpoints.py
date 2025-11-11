"""
Persona API - Orchestration Streaming

Moduł obsługujący SSE (Server-Sent Events) streaming dla generacji person.
Zawiera generatory dla real-time progress tracking podczas generacji.
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from app.models import GenerationProgress, GenerationStage
from config import features

# Import będzie dodany po utworzeniu validation_endpoints.py
# from .validation_endpoints import _generate_personas_task


logger = logging.getLogger(__name__)


# ===== SSE STREAMING WRAPPER =====

async def _generate_personas_task_streaming(
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
    advanced_options: dict[str, Any] | None = None,
    use_rag: bool = True,
):
    """
    Streaming wrapper dla _generate_personas_task z progress tracking.

    Generator który yield'uje GenerationProgress events podczas generacji person.
    Używa kolejki (asyncio.Queue) do komunikacji między zadaniem generacji
    a SSE stream.

    ARCHITEKTURA:
    1. Tworzy asyncio.Queue dla progress events
    2. Uruchamia _generate_personas_task_with_progress w tle (przekazując queue)
    3. Yield'uje progress events z kolejki do SSE stream
    4. Obsługuje cleanup po zakończeniu

    Args:
        project_id: UUID projektu
        num_personas: Liczba person do wygenerowania
        adversarial_mode: Czy użyć adversarial prompting
        advanced_options: Zaawansowane opcje generacji
        use_rag: Czy użyć RAG context

    Yields:
        GenerationProgress: Progress events dla SSE stream
    """
    # Kolejka dla progress events (producer: task, consumer: SSE stream)
    progress_queue: asyncio.Queue[GenerationProgress | None] = asyncio.Queue()

    async def progress_callback(progress: GenerationProgress):
        """Callback wywoływany przez task - dodaje event do kolejki."""
        await progress_queue.put(progress)

    # Uruchom zadanie generacji w tle z progress callback
    task = asyncio.create_task(
        _generate_personas_task_with_progress(
            project_id=project_id,
            num_personas=num_personas,
            adversarial_mode=adversarial_mode,
            advanced_options=advanced_options,
            use_rag=use_rag,
            progress_callback=progress_callback,
        )
    )

    try:
        # Yield progress events z kolejki
        while True:
            # Timeout 60s - jeśli brak progressu przez minutę, yield heartbeat
            try:
                progress = await asyncio.wait_for(progress_queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                # Heartbeat - keep connection alive (Cloud Run compatibility)
                logger.debug("SSE heartbeat (no progress for 60s)")
                continue

            # None oznacza koniec stream
            if progress is None:
                logger.info("SSE stream completed (task finished)")
                break

            # Yield progress event
            yield progress

            # Jeśli completed lub failed, zakończ stream
            if progress.stage in [GenerationStage.COMPLETED, GenerationStage.FAILED]:
                break

    finally:
        # Cleanup: poczekaj na zakończenie zadania
        if not task.done():
            logger.warning("SSE stream closing while task still running - waiting for task completion")
            await task


async def _generate_personas_task_with_progress(
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
    advanced_options: dict[str, Any] | None = None,
    use_rag: bool = True,
    progress_callback: Any | None = None,
):
    """
    Rozszerzona wersja _generate_personas_task z progress tracking.

    UWAGA: To jest UPROSZCZONA wersja która deleguje większość logiki do
    oryginalnego _generate_personas_task i dodaje tylko progress tracking.

    Dla pełnego streaming z real-time progress w KAŻDYM kroku, potrzebujemy
    zmodyfikować oryginalną funkcję - to wymaga refactoringu 780+ linii kodu.

    CURRENT APPROACH (MVP):
    - Yield initial progress (0%)
    - Delegate to _generate_personas_task (black box - no intermediate progress)
    - Yield completion progress (100%)

    FUTURE IMPROVEMENT (requires refactoring):
    - Extract generation logic into smaller functions
    - Yield progress after each step (orchestration, batches, validation, etc.)

    Args:
        project_id: UUID projektu
        num_personas: Liczba person do wygenerowania
        adversarial_mode: Czy użyć adversarial prompting
        advanced_options: Zaawansowane opcje generacji
        use_rag: Czy użyć RAG context
        progress_callback: Opcjonalny callback dla progress events
    """
    # Import lokalny aby uniknąć circular import
    from .validation_endpoints import _generate_personas_task

    try:
        # Stage 1: Initializing (0-5%)
        if progress_callback:
            await progress_callback(GenerationProgress(
                stage=GenerationStage.INITIALIZING,
                progress_percent=5,
                message="Ładowanie projektu i konfiguracji...",
                total_personas=num_personas,
                personas_generated=0,
            ))

        # Stage 2: Orchestration (5-20%)
        # TODO: Extract orchestration from _generate_personas_task for real-time progress
        if progress_callback and use_rag and features.orchestration.enabled:
            await progress_callback(GenerationProgress(
                stage=GenerationStage.ORCHESTRATION,
                progress_percent=5,
                message="Tworzenie briefów segmentów (Gemini 2.5 Pro + Graph RAG)...",
                total_personas=num_personas,
                personas_generated=0,
            ))

        # Delegate to original task (black box - no progress tracking inside)
        # TODO: Refactor _generate_personas_task to accept progress_callback
        logger.info(f"Delegating to _generate_personas_task (project={project_id}, personas={num_personas})")

        if progress_callback:
            await progress_callback(GenerationProgress(
                stage=GenerationStage.GENERATING_PERSONAS,
                progress_percent=20,
                message=f"Generowanie {num_personas} person (równoległe wywołania LLM)...",
                total_personas=num_personas,
                personas_generated=0,
            ))

        # Call original task (this blocks until all personas are generated)
        await _generate_personas_task(
            project_id=project_id,
            num_personas=num_personas,
            adversarial_mode=adversarial_mode,
            advanced_options=advanced_options,
            use_rag=use_rag,
        )

        # Stage 3: Completed (100%)
        if progress_callback:
            await progress_callback(GenerationProgress(
                stage=GenerationStage.COMPLETED,
                progress_percent=100,
                message=f"Generacja {num_personas} person zakończona pomyślnie!",
                total_personas=num_personas,
                personas_generated=num_personas,
            ))

            # Signal end of stream
            await progress_callback(None)

    except Exception as e:
        logger.error(
            "Persona generation with progress tracking FAILED",
            exc_info=True,
            extra={
                "project_id": str(project_id),
                "num_personas": num_personas,
                "error_type": type(e).__name__,
                "error_message": str(e)[:500],
            }
        )

        # Stage: Failed
        if progress_callback:
            await progress_callback(GenerationProgress(
                stage=GenerationStage.FAILED,
                progress_percent=0,
                message=f"Błąd generacji: {str(e)[:200]}",
                total_personas=num_personas,
                personas_generated=0,
                error=str(e)[:500],
            ))

            # Signal end of stream
            await progress_callback(None)

        raise
