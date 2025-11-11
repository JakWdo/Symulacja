"""Serwis orkiestracji generowania person używający Gemini 2.5 Pro.

Ten moduł zawiera `PersonaOrchestrationService`, który wykorzystuje Gemini 2.5 Pro
do przeprowadzenia głębokiej analizy Graph RAG i tworzenia szczegółowych briefów
(900-1200 znaków) dla każdej grupy demograficznej person.

Filozofia:
- Orchestration Agent (Gemini 2.5 Pro) = complex reasoning, długie analizy
- Individual Generators (Gemini 2.5 Flash) = szybkie generowanie konkretnych person
- Output style: Edukacyjny - wyjaśnia "dlaczego", konwersacyjny ton

Wszystkie helper functions i models przeniesione do orchestration/ subpackage.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.shared import build_chat_model, get_polish_society_rag
from .orchestration import (
    PersonaAllocationPlan,
    get_comprehensive_graph_context,
    build_orchestration_prompt,
    extract_json_from_response,
)

logger = logging.getLogger(__name__)


class PersonaOrchestrationService:
    """Serwis orkiestracji używający Gemini 2.5 Pro do tworzenia briefów.

    Ten serwis:
    1. Pobiera comprehensive Graph RAG context (Wskazniki, Grupy_Demograficzne, Trendy)
    2. Przeprowadza głęboką socjologiczną analizę używając Gemini 2.5 Pro
    3. Tworzy szczegółowe briefe (900-1200 znaków) dla każdej grupy person
    4. Wyjaśnia "dlaczego" (edukacyjny output style) dla wszystkich decyzji

    Output style: Konwersacyjny, edukacyjny, wyjaśniający, production-ready.
    """

    def __init__(self) -> None:
        """Inicjalizuje orchestration agent (Gemini 2.5 Pro) i RAG service."""
        from config import models

        # Model config z centralnego registry
        model_config = models.get("personas", "orchestration")
        self.llm = build_chat_model(**model_config.params)

        # RAG service dla hybrid search kontekstu (singleton)
        self.rag_service = get_polish_society_rag()

        logger.info(
            "PersonaOrchestrationService zainicjalizowany (%s)",
            model_config.model
        )

    async def create_persona_allocation_plan(
        self,
        target_demographics: dict[str, Any],
        num_personas: int,
        project_description: str | None = None,
        additional_context: str | None = None,
    ) -> PersonaAllocationPlan:
        """Tworzy szczegółowy plan alokacji person z długimi briefami.

        Gemini 2.5 Pro przeprowadza głęboką analizę:
        1. Pobiera Graph RAG context (hybrid search dla rozkładów demograficznych)
        2. Analizuje trendy społeczne i wskaźniki statystyczne
        3. Tworzy spójne (900-1200 znaków) edukacyjne briefe
        4. Wyjaśnia "dlaczego" dla każdej decyzji alokacyjnej

        Args:
            target_demographics: Rozkład demograficzny projektu (age_group, gender, etc.)
            num_personas: Całkowita liczba person do wygenerowania
            project_description: Opis projektu badawczego
            additional_context: Dodatkowy kontekst od użytkownika (z AI Wizard)

        Returns:
            PersonaAllocationPlan z grupami demograficznymi i szczegółowymi briefami

        Raises:
            Exception: Jeśli LLM nie może wygenerować planu lub JSON parsing fails
        """
        import time

        # === TIMING & MONITORING ===
        start_time = time.time()
        logger.info(f"🎯 Orchestration START: Creating allocation plan for {num_personas} personas")

        try:
            # Krok 1: Pobierz comprehensive Graph RAG context
            graph_start = time.time()
            graph_context = await get_comprehensive_graph_context(
                target_demographics,
                self.rag_service
            )
            graph_duration = time.time() - graph_start

            logger.info(
                f"📊 Graph RAG completed: {len(graph_context)} chars in {graph_duration:.2f}s"
            )

            # Krok 2: Zbuduj prompt w stylu edukacyjnym
            prompt = build_orchestration_prompt(
                num_personas=num_personas,
                target_demographics=target_demographics,
                graph_context=graph_context,
                project_description=project_description,
                additional_context=additional_context,
            )

            # Krok 3: Gemini 2.5 Pro generuje plan (długa analiza)
            llm_start = time.time()
            logger.info("🤖 Invoking Gemini 2.5 Pro for orchestration (max_tokens=8000)...")
            response = await self.llm.ainvoke(prompt)
            llm_duration = time.time() - llm_start

            # DEBUG: Log surowej odpowiedzi od Gemini
            response_text = response.content if hasattr(response, 'content') else str(response)
            logger.info(
                f"📝 Gemini response: {len(response_text)} chars in {llm_duration:.2f}s"
            )
            logger.debug(f"📝 Response preview (first 500 chars): {response_text[:500]}")

            # Parse JSON response
            parsing_start = time.time()
            plan_json = extract_json_from_response(response_text)
            parsing_duration = time.time() - parsing_start

            logger.debug(f"✅ JSON parsed in {parsing_duration:.2f}s: {len(plan_json)} top-level keys")

            # Parse do Pydantic model (walidacja)
            plan = PersonaAllocationPlan(**plan_json)

            # === TIMING METRICS (SUCCESS) ===
            total_duration = time.time() - start_time

            logger.info(
                f"✅ Orchestration COMPLETED in {total_duration:.2f}s "
                f"(graph={graph_duration:.2f}s, llm={llm_duration:.2f}s, parsing={parsing_duration:.2f}s)"
            )

            # Structured metrics for monitoring
            logger.info(
                "METRICS_ORCHESTRATION",
                extra={
                    "metric_type": "orchestration_performance",
                    "total_duration_seconds": total_duration,
                    "graph_rag_duration_seconds": graph_duration,
                    "llm_duration_seconds": llm_duration,
                    "parsing_duration_seconds": parsing_duration,
                    "num_personas": num_personas,
                    "num_groups": len(plan.groups),
                    "graph_context_chars": len(graph_context),
                    "response_chars": len(response_text),
                    "success": True,
                }
            )

            return plan

        except Exception as e:
            # === TIMING METRICS (FAILURE) ===
            total_duration = time.time() - start_time

            logger.error(
                f"❌ Orchestration FAILED after {total_duration:.2f}s: {e}",
                exc_info=True
            )

            # Structured metrics for monitoring
            logger.error(
                "METRICS_ORCHESTRATION",
                extra={
                    "metric_type": "orchestration_performance",
                    "total_duration_seconds": total_duration,
                    "num_personas": num_personas,
                    "success": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:500],
                }
            )
            raise
