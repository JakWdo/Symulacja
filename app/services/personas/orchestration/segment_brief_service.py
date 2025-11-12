"""SegmentBriefService - generowanie i cache'owanie briefów segmentów.

Ten serwis zarządza:
1. Generowaniem długich, ciekawych opisów segmentów społecznych (SegmentBrief)
2. Cache'owaniem briefów w Redis (TTL 7 dni, wspólny dla wszystkich person w segmencie)
3. Generowaniem opisów unikalności person ("Dlaczego ta osoba jest wyjątkowa")

Architecture:
- segment_id = hash(age, education, location, gender, income)
- Brief jest wspólny dla wszystkich person w projekcie z tym samym segment_id
- Redis cache: segment_brief:{project_id}:{segment_id}
- Hybrid generation: demografia + RAG + przykładowe persony z segmentu
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import models, app
from app.models.persona import Persona
from app.schemas.segment_brief import (
    SegmentBrief,
    SegmentBriefRequest,
    SegmentBriefResponse,
)
from app.services.shared import build_chat_model, get_polish_society_rag
from app.services.personas.orchestration.brief_cache import (
    get_from_cache,
    save_to_cache,
    get_cache_ttl,
)
from app.services.personas.orchestration.brief_formatter import (
    format_example_personas,
    generate_segment_name,
    build_segment_brief_prompt,
    generate_social_context,
    extract_characteristics,
    generate_fallback_brief,
    generate_persona_uniqueness,
)

logger = logging.getLogger(__name__)


class SegmentBriefService:
    """Serwis do generowania i cache'owania briefów segmentów społecznych.

    Responsibilities:
    1. Generate segment briefs (długie, ciekawe opisy segmentów)
    2. Cache briefs in Redis (TTL 7 days, shared across personas in segment)
    3. Generate persona uniqueness descriptions
    4. Hybrid approach: demographics + RAG + example personas

    Performance:
    - Cache hit: < 50ms
    - Cache miss (generation): < 5s (depends on RAG query + LLM)
    - Redis TTL: 7 days (604800 seconds)
    """

    def __init__(self, db: AsyncSession):
        """Inicjalizuje serwis z LLM i RAG.

        Args:
            db: AsyncSession dla dostępu do bazy danych
        """
        self.db = db

        # Model config z centralnego registry
        model_config = models.get("personas", "segment_brief")
        self.llm = build_chat_model(**model_config.params)

        # RAG dla kontekstu społecznego Polski (singleton)
        self.rag_service = get_polish_society_rag()

        # Redis dla cache (używamy tego samego co w innych miejscach)
        self.redis_client = None
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                app.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("✅ SegmentBriefService: Redis połączony")
        except Exception as exc:
            logger.warning(
                "⚠️ SegmentBriefService: Redis niedostępny - cache wyłączony. Error: %s",
                exc
            )

    @staticmethod
    def generate_segment_id(demographics: dict[str, Any]) -> str:
        """Generuje unikalny ID segmentu z demografii.

        Segment ID to hash demografii - wszystkie persony z tymi samymi
        cechami demograficznymi należą do tego samego segmentu.

        Args:
            demographics: Dict z age, gender, education, location, income

        Returns:
            segment_id (np. "seg_25-34_wyższe_warszawa_kobieta")

        Example:
            >>> demographics = {
            ...     "age": "25-34",
            ...     "gender": "kobieta",
            ...     "education": "wyższe",
            ...     "location": "Warszawa",
            ...     "income": "7 500 - 10 000 zł"
            ... }
            >>> generate_segment_id(demographics)
            'seg_25-34_wyższe_warszawa_kobieta'
        """
        # Normalizuj klucze (niektóre mogą być age_group vs age, etc.)
        age = demographics.get("age") or demographics.get("age_group", "unknown")
        gender = demographics.get("gender", "unknown")
        education = demographics.get("education") or demographics.get("education_level", "unknown")
        location = demographics.get("location", "unknown")
        income = demographics.get("income") or demographics.get("income_bracket", "unknown")

        # Sanitize i lowercase dla spójności
        age = str(age).lower().replace(" ", "-")
        gender = str(gender).lower().replace(" ", "-")
        education = str(education).lower().replace(" ", "-")
        location = str(location).lower().replace(" ", "-")
        income = str(income).lower().replace(" ", "-")

        # Skrócona wersja dla czytelności (zamiast hash)
        segment_id = f"seg_{age}_{education}_{location}_{gender}"

        return segment_id

    async def _get_example_personas_from_segment(
        self,
        project_id: UUID,
        segment_id: str,
        max_personas: int = 3
    ) -> list[Persona]:
        """Pobiera przykładowe persony z danego segmentu dla projektu.

        Args:
            project_id: UUID projektu
            segment_id: ID segmentu
            max_personas: Max liczba person do pobrania

        Returns:
            Lista person (max 3)
        """
        try:
            result = await self.db.execute(
                select(Persona)
                .where(
                    Persona.project_id == project_id,
                    Persona.segment_id == segment_id,
                    Persona.deleted_at.is_(None)  # Tylko aktywne persony
                )
                .limit(max_personas)
            )
            personas = result.scalars().all()

            logger.info(
                "📊 Znaleziono %s przykładowych person dla segmentu '%s'",
                len(personas),
                segment_id
            )

            return personas

        except Exception as exc:
            logger.warning(
                "⚠️ Błąd pobierania przykładowych person dla segmentu %s: %s",
                segment_id,
                exc
            )
            return []

    async def _fetch_rag_context(self, demographics: dict[str, Any]) -> str:
        """Pobiera kontekst RAG dla demografii segmentu.

        Args:
            demographics: Dict z age, gender, education, location, income

        Returns:
            Sformatowany kontekst z RAG (max 1500 chars)
        """
        if not self.rag_service or not self.rag_service.vector_store:
            logger.warning("RAG service niedostępny - kontekst pusty")
            return "Brak dostępnego kontekstu RAG."

        # Buduj query z demografii
        age = demographics.get("age") or demographics.get("age_group", "")
        gender = demographics.get("gender", "")
        education = demographics.get("education") or demographics.get("education_level", "")
        location = demographics.get("location", "")

        query = f"demographics statistics Poland {age} {gender} {education} {location}"

        try:
            # Hybrid search (top 5 results)
            documents = await self.rag_service.hybrid_search(query=query, top_k=5)

            # Formatuj kontekst
            if not documents:
                return "Brak danych RAG dla tej demografii."

            formatted = "=== KONTEKST Z RAG (Polskie dane społeczne) ===\n\n"
            for idx, doc in enumerate(documents[:5], 1):
                content = doc.page_content[:250]  # Max 250 chars per doc
                formatted += f"[{idx}] {content}\n\n"

            # Truncate do 1500 chars total
            if len(formatted) > 1500:
                formatted = formatted[:1500] + "..."

            logger.info("✅ RAG context pobrano: %s znaków", len(formatted))
            return formatted

        except Exception as exc:
            logger.warning("⚠️ Błąd pobierania RAG context: %s", exc)
            return "Błąd podczas pobierania kontekstu RAG."

    async def generate_segment_brief(
        self,
        demographics: dict[str, Any],
        project_id: UUID,
        max_example_personas: int = 3,
        force_refresh: bool = False
    ) -> SegmentBrief:
        """Generuje lub pobiera z cache segment brief.

        Flow:
        1. Wygeneruj segment_id z demografii
        2. Sprawdź cache (jeśli !force_refresh)
        3. Jeśli cache miss:
           a. Pobierz RAG context
           b. Pobierz przykładowe persony z segmentu
           c. Wygeneruj brief przez LLM (Gemini 2.5 Pro)
           d. Zapisz do cache
        4. Zwróć brief

        Args:
            demographics: Dict z age, gender, education, location, income
            project_id: UUID projektu
            max_example_personas: Max liczba przykładowych person
            force_refresh: Czy pominąć cache i wygenerować na nowo

        Returns:
            SegmentBrief

        Performance:
            - Cache hit: < 50ms
            - Cache miss: < 5s (RAG + LLM)
        """
        import time
        start_time = time.time()

        # 1. Wygeneruj segment_id
        segment_id = self.generate_segment_id(demographics)
        logger.info(
            "🎯 Generowanie segment brief dla: %s (project: %s)",
            segment_id,
            project_id
        )

        # 2. Sprawdź cache (jeśli !force_refresh)
        if not force_refresh:
            cached_brief = await get_from_cache(
                self.redis_client, str(project_id), segment_id
            )
            if cached_brief:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    "✅ Segment brief z cache (elapsed: %sms)",
                    elapsed_ms
                )
                return cached_brief

        # 3. Cache miss - generuj brief
        logger.info("🤖 Generowanie nowego segment brief (LLM + RAG)...")

        # 3a. Pobierz RAG context
        rag_context = await self._fetch_rag_context(demographics)

        # 3b. Pobierz przykładowe persony
        example_personas = await self._get_example_personas_from_segment(
            project_id, segment_id, max_example_personas
        )
        example_personas_text = format_example_personas(example_personas)

        # 3c. Wygeneruj segment name (krótka nazwa segmentu)
        segment_name = await generate_segment_name(demographics, rag_context)

        # 3d. Zbuduj prompt dla segment brief
        prompt = build_segment_brief_prompt(
            segment_name=segment_name,
            demographics=demographics,
            rag_context=rag_context,
            example_personas=example_personas_text
        )

        # 3e. Wywołaj LLM
        try:
            response = await self.llm.ainvoke(prompt)
            description = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # Walidacja długości (400-800 słów = ~2400-4800 znaków)
            if len(description) < 1000:
                logger.warning(
                    "⚠️ Generated brief zbyt krótki (%s chars) - mogło być przerwane",
                    len(description)
                )
            elif len(description) > 6000:
                logger.warning(
                    "⚠️ Generated brief zbyt długi (%s chars) - obcięcie do 5000",
                    len(description)
                )
                description = description[:5000]

        except Exception as exc:
            logger.error("❌ Błąd generowania segment brief: %s", exc, exc_info=True)
            # Fallback minimal brief
            description = generate_fallback_brief(segment_name, demographics)

        # 3f. Wygeneruj social_context i characteristics
        social_context = await generate_social_context(
            segment_name, demographics, rag_context
        )
        characteristics = extract_characteristics(demographics, rag_context)

        # 3g. Stwórz SegmentBrief object
        brief = SegmentBrief(
            segment_id=segment_id,
            segment_name=segment_name,
            description=description,
            social_context=social_context,
            characteristics=characteristics,
            based_on_personas_count=len(example_personas),
            demographics=demographics,
            generated_at=datetime.now(timezone.utc),
            generated_by="gemini-2.5-pro"
        )

        # 4. Zapisz do cache
        await save_to_cache(self.redis_client, str(project_id), segment_id, brief)

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "✅ Segment brief wygenerowany (elapsed: %sms, length: %s chars)",
            elapsed_ms,
            len(description)
        )

        return brief

    async def generate_persona_uniqueness(
        self,
        persona: Persona,
        segment_brief: SegmentBrief
    ) -> str:
        """Generuje opis unikalności persony w kontekście segmentu.

        Args:
            persona: Persona object
            segment_brief: Brief segmentu do którego należy persona

        Returns:
            Opis unikalności (2-4 zdania, max 300 znaków)
        """
        return await generate_persona_uniqueness(persona, segment_brief)

    async def get_or_generate_segment_brief(
        self,
        request: SegmentBriefRequest
    ) -> SegmentBriefResponse:
        """Public API: Pobiera segment brief z cache lub generuje nowy.

        Args:
            request: SegmentBriefRequest

        Returns:
            SegmentBriefResponse z briefem i metadanymi cache
        """
        project_id = UUID(request.project_id)

        # Generuj brief
        brief = await self.generate_segment_brief(
            demographics=request.demographics,
            project_id=project_id,
            max_example_personas=request.max_example_personas,
            force_refresh=request.force_refresh
        )

        # Sprawdź czy z cache
        from_cache = not request.force_refresh
        if from_cache and self.redis_client:
            # Sprawdź TTL
            cache_ttl_seconds = await get_cache_ttl(
                self.redis_client, str(project_id), brief.segment_id
            )
        else:
            cache_ttl_seconds = None

        return SegmentBriefResponse(
            brief=brief,
            from_cache=from_cache,
            cache_ttl_seconds=cache_ttl_seconds
        )
