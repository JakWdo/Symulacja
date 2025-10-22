"""
SegmentBriefService - generowanie i cache'owanie briefów segmentów.

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

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.prompts.persona_prompts import (
    SEGMENT_BRIEF_PROMPT_TEMPLATE,
    PERSONA_UNIQUENESS_PROMPT_TEMPLATE,
)
from app.core.prompts.system_prompts import (
    POLISH_SOCIETY_EXPERT_PROMPT,
    CONVERSATIONAL_TONE_PROMPT,
    STORYTELLING_PROMPT,
    build_system_prompt,
)
from app.core.redis import get_redis_client, redis_get_json, redis_set_json
from app.models.persona import Persona
from app.schemas.segment_brief import (
    SegmentBrief,
    SegmentBriefRequest,
    SegmentBriefResponse,
)
from app.services.shared.clients import build_chat_model
from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG

settings = get_settings()
logger = logging.getLogger(__name__)


class SegmentBriefService:
    """
    Serwis do generowania i cache'owania briefów segmentów społecznych.

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
        """
        Inicjalizuje serwis z LLM i RAG.

        Args:
            db: AsyncSession dla dostępu do bazy danych
        """
        self.db = db

        # LLM dla generowania briefów (Gemini 2.5 Pro dla wysokiej jakości)
        self.llm = build_chat_model(
            model="gemini-2.5-pro",
            temperature=0.7,  # Wyższa dla kreatywnego storytelling
            max_tokens=6000,  # Długie briefe (400-800 słów)
            timeout=120,
        )

        # RAG dla kontekstu społecznego Polski
        self.rag_service = PolishSocietyRAG()

        # Cache TTL (7 dni)
        self.CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800 sekund

    @staticmethod
    def generate_segment_id(demographics: dict[str, Any]) -> str:
        """
        Generuje unikalny ID segmentu z demografii.

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

    def _get_cache_key(self, project_id: str, segment_id: str) -> str:
        """Tworzy klucz Redis dla segment brief."""
        return f"segment_brief:{project_id}:{segment_id}"

    async def _get_from_cache(
        self, project_id: str, segment_id: str
    ) -> SegmentBrief | None:
        """
        Pobiera segment brief z Redis cache.

        Args:
            project_id: UUID projektu
            segment_id: ID segmentu

        Returns:
            SegmentBrief jeśli w cache, None jeśli nie ma
        """
        cache_key = self._get_cache_key(project_id, segment_id)

        try:
            brief_dict = await redis_get_json(cache_key)
            if brief_dict:
                logger.info(
                    "✅ Cache HIT: Segment brief '%s' dla projektu %s",
                    segment_id,
                    project_id
                )
                return SegmentBrief(**brief_dict)

            logger.info(
                "❌ Cache MISS: Segment brief '%s' dla projektu %s",
                segment_id,
                project_id
            )
            return None

        except Exception as exc:
            logger.warning(
                "⚠️ Błąd odczytu z cache dla %s: %s",
                cache_key,
                exc
            )
            return None

    async def _save_to_cache(
        self,
        project_id: str,
        segment_id: str,
        brief: SegmentBrief
    ) -> None:
        """
        Zapisuje segment brief do Redis cache.

        Args:
            project_id: UUID projektu
            segment_id: ID segmentu
            brief: SegmentBrief do zapisania
        """
        cache_key = self._get_cache_key(project_id, segment_id)

        try:
            # Zapisz z TTL (redis_set_json obsługuje Pydantic models)
            await redis_set_json(
                cache_key,
                brief.model_dump(mode="json"),
                ttl_seconds=self.CACHE_TTL_SECONDS
            )

            logger.info(
                "💾 Cache SAVE: Segment brief '%s' dla projektu %s (TTL: %s dni)",
                segment_id,
                project_id,
                self.CACHE_TTL_SECONDS // 86400
            )

        except Exception as exc:
            logger.warning(
                "⚠️ Błąd zapisu do cache dla %s: %s",
                cache_key,
                exc
            )

    async def _get_example_personas_from_segment(
        self,
        project_id: UUID,
        segment_id: str,
        max_personas: int = 3
    ) -> list[Persona]:
        """
        Pobiera przykładowe persony z danego segmentu dla projektu.

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
        """
        Pobiera kontekst RAG dla demografii segmentu.

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

    def _format_example_personas(self, personas: list[Persona]) -> str:
        """
        Formatuje przykładowe persony do prompta.

        Args:
            personas: Lista person

        Returns:
            Sformatowany string z przykładami
        """
        if not personas:
            return "Brak przykładowych person z tego segmentu."

        formatted = "=== PRZYKŁADOWE PERSONY Z TEGO SEGMENTU ===\n\n"

        for idx, persona in enumerate(personas, 1):
            formatted += f"**Persona {idx}: {persona.full_name}**\n"
            formatted += f"- Wiek: {persona.age}, Zawód: {persona.occupation}\n"
            formatted += f"- Wykształcenie: {persona.education_level}\n"
            formatted += f"- Dochód: {persona.income_bracket}\n"

            # Skrócony background (max 200 chars)
            if persona.background_story:
                bg_short = persona.background_story[:200]
                if len(persona.background_story) > 200:
                    bg_short += "..."
                formatted += f"- Historia: {bg_short}\n"

            # Wartości (top 3)
            if persona.values:
                values_str = ", ".join(persona.values[:3])
                formatted += f"- Wartości: {values_str}\n"

            formatted += "\n"

        return formatted

    async def generate_segment_brief(
        self,
        demographics: dict[str, Any],
        project_id: UUID,
        max_example_personas: int = 3,
        force_refresh: bool = False
    ) -> SegmentBrief:
        """
        Generuje lub pobiera z cache segment brief.

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
            cached_brief = await self._get_from_cache(str(project_id), segment_id)
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
        example_personas_text = self._format_example_personas(example_personas)

        # 3c. Wygeneruj segment name (krótka nazwa segmentu)
        segment_name = await self._generate_segment_name(demographics, rag_context)

        # 3d. Zbuduj prompt dla segment brief
        prompt = self._build_segment_brief_prompt(
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
            description = self._generate_fallback_brief(segment_name, demographics)

        # 3f. Wygeneruj social_context i characteristics
        social_context = await self._generate_social_context(
            segment_name, demographics, rag_context
        )
        characteristics = self._extract_characteristics(demographics, rag_context)

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
        await self._save_to_cache(str(project_id), segment_id, brief)

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "✅ Segment brief wygenerowany (elapsed: %sms, length: %s chars)",
            elapsed_ms,
            len(description)
        )

        return brief

    async def _generate_segment_name(
        self,
        demographics: dict[str, Any],
        rag_context: str
    ) -> str:
        """
        Generuje mówiącą nazwę segmentu (np. 'Młodzi Prekariusze').

        Args:
            demographics: Demografia segmentu
            rag_context: Kontekst RAG

        Returns:
            Nazwa segmentu (5-60 chars)
        """
        age = demographics.get("age") or demographics.get("age_group", "unknown")
        gender = demographics.get("gender", "unknown")
        education = demographics.get("education") or demographics.get("education_level", "unknown")
        income = demographics.get("income") or demographics.get("income_bracket", "unknown")

        # Skrócony RAG context (max 200 chars)
        rag_short = rag_context[:200] if rag_context else "Brak"

        prompt = f"""Stwórz trafną, MÓWIĄCĄ nazwę dla segmentu demograficznego.

DEMOGRAFIA:
- Wiek: {age}
- Płeć: {gender}
- Wykształcenie: {education}
- Dochód: {income}

RAG INSIGHTS:
{rag_short}

ZASADY:
- 2-4 słowa (np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44")
- Oddaje kluczową charakterystykę (wiek + status społeczno-ekonomiczny)
- Polski język, naturalnie brzmi
- Unikaj ogólników

ZWRÓĆ TYLKO NAZWĘ (bez cudzysłowów):"""

        try:
            # Gemini Flash dla szybkiego naming
            llm_flash = build_chat_model(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
                max_tokens=50,
                timeout=10,
            )

            response = await llm_flash.ainvoke(prompt)
            name = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            name = name.strip('"\'')  # Remove quotes

            # Walidacja (5-60 chars)
            if 5 <= len(name) <= 60:
                return name

            # Fallback
            logger.warning("Generated name invalid length: '%s' - using fallback", name)

        except Exception as exc:
            logger.warning("Błąd generowania segment name: %s - using fallback", exc)

        # Fallback name
        return f"Segment {age}, {gender}"

    def _build_segment_brief_prompt(
        self,
        segment_name: str,
        demographics: dict[str, Any],
        rag_context: str,
        example_personas: str
    ) -> str:
        """Buduje prompt dla generowania segment brief."""

        age_range = demographics.get("age") or demographics.get("age_group", "unknown")
        gender = demographics.get("gender", "unknown")
        education = demographics.get("education") or demographics.get("education_level", "unknown")
        location = demographics.get("location", "unknown")
        income = demographics.get("income") or demographics.get("income_bracket", "unknown")

        # System prompt z storytelling approach
        system_prompt = build_system_prompt(
            POLISH_SOCIETY_EXPERT_PROMPT,
            STORYTELLING_PROMPT,
            CONVERSATIONAL_TONE_PROMPT
        )

        # User prompt (SEGMENT_BRIEF_PROMPT_TEMPLATE z persona_prompts.py)
        user_prompt = SEGMENT_BRIEF_PROMPT_TEMPLATE.format(
            segment_name=segment_name,
            age_range=age_range,
            gender=gender,
            education=education,
            location=location,
            income=income,
            rag_context=rag_context,
            example_personas=example_personas
        )

        return f"{system_prompt}\n\n{user_prompt}"

    async def _generate_social_context(
        self,
        segment_name: str,
        demographics: dict[str, Any],
        rag_context: str
    ) -> str:
        """
        Generuje social context (300-500 słów).

        Args:
            segment_name: Nazwa segmentu
            demographics: Demografia
            rag_context: Kontekst RAG

        Returns:
            Social context string
        """
        # Dla prostoty, wyekstraktujemy to z głównego briefu lub użyjemy uproszczonej wersji
        # W produkcji można to wygenerować osobnym LLM callem
        age = demographics.get("age") or demographics.get("age_group", "unknown")
        education = demographics.get("education") or demographics.get("education_level", "unknown")
        location = demographics.get("location", "unknown")

        return (
            f"Segment '{segment_name}' charakteryzuje się specyficznym kontekstem społeczno-ekonomicznym. "
            f"Osoby w wieku {age}, z wykształceniem {education}, mieszkające w lokalizacji {location}, "
            f"znajdują się w unikalnym momencie życia, który kształtuje ich wartości, aspiracje i wyzwania."
        )

    def _extract_characteristics(
        self,
        demographics: dict[str, Any],
        rag_context: str
    ) -> list[str]:
        """
        Ekstraktuje 5-7 kluczowych cech segmentu.

        Args:
            demographics: Demografia
            rag_context: Kontekst RAG

        Returns:
            Lista cech (strings)
        """
        characteristics = []

        # Z demografii
        age = demographics.get("age") or demographics.get("age_group", "")
        if "25-34" in str(age):
            characteristics.append("Młodzi profesjonaliści")
        elif "35-44" in str(age):
            characteristics.append("Established professionals")

        education = demographics.get("education") or demographics.get("education_level", "")
        if "wyższe" in str(education).lower() or "magisterskie" in str(education).lower():
            characteristics.append("Wysoko wykształceni")

        location = demographics.get("location", "")
        if location.lower() in ["warszawa", "kraków", "wrocław", "gdańsk", "poznań"]:
            characteristics.append("Mieszkańcy dużych miast")

        # Domyślne cechy (jeśli za mało)
        if len(characteristics) < 3:
            characteristics.extend([
                "Aktywni zawodowo",
                "Otwarci na zmiany",
                "Konsumenci świadomi"
            ])

        return characteristics[:7]  # Max 7

    def _generate_fallback_brief(
        self,
        segment_name: str,
        demographics: dict[str, Any]
    ) -> str:
        """Fallback brief gdy LLM zawiedzie."""
        age = demographics.get("age") or demographics.get("age_group", "unknown")
        education = demographics.get("education") or demographics.get("education_level", "unknown")
        location = demographics.get("location", "unknown")

        return (
            f"Segment '{segment_name}' obejmuje osoby w wieku {age}, "
            f"z wykształceniem {education}, mieszkające w {location}. "
            f"Ta grupa demograficzna stanowi istotną część polskiego społeczeństwa "
            f"i charakteryzuje się specyficznymi wartościami, aspiracjami oraz wyzwaniami życiowymi."
        )

    async def generate_persona_uniqueness(
        self,
        persona: Persona,
        segment_brief: SegmentBrief
    ) -> str:
        """
        Generuje opis unikalności persony w kontekście segmentu.

        Args:
            persona: Persona object
            segment_brief: Brief segmentu do którego należy persona

        Returns:
            Opis unikalności (2-4 zdania, max 300 znaków)
        """
        # Skróć segment brief summary (max 500 chars)
        brief_summary = segment_brief.description[:500]
        if len(segment_brief.description) > 500:
            brief_summary += "..."

        # Format values i interests
        values_str = ", ".join(persona.values[:3]) if persona.values else "brak danych"
        interests_str = ", ".join(persona.interests[:3]) if persona.interests else "brak danych"

        # Skróć background (max 400 chars)
        background = persona.background_story[:400] if persona.background_story else "Brak historii"
        if persona.background_story and len(persona.background_story) > 400:
            background += "..."

        # Użyj segment_name z persony (z orchestration) dla consistency
        # segment_brief.segment_name może być inne (generowane dynamicznie przez LLM)
        segment_name_to_use = persona.segment_name or segment_brief.segment_name

        # Prompt (PERSONA_UNIQUENESS_PROMPT_TEMPLATE z persona_prompts.py)
        prompt = PERSONA_UNIQUENESS_PROMPT_TEMPLATE.format(
            persona_name=persona.full_name or "Ta osoba",
            segment_name=segment_name_to_use,
            age=persona.age,
            occupation=persona.occupation or "brak danych",
            background_story=background,
            values=values_str,
            interests=interests_str,
            segment_brief_summary=brief_summary
        )

        try:
            # Gemini Flash dla szybkiego generowania
            llm_flash = build_chat_model(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
                max_tokens=600,  # 3-4 akapity (250-400 słów)
                timeout=20,
            )

            response = await llm_flash.ainvoke(prompt)
            uniqueness = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # Brak limitu długości - AI dostaje pełną swobodę (250-400 słów jak w promptcie)

            logger.info(
                "✅ Persona uniqueness wygenerowana dla %s (length: %s chars)",
                persona.full_name,
                len(uniqueness)
            )

            return uniqueness

        except Exception as exc:
            logger.warning(
                "⚠️ Błąd generowania persona uniqueness dla %s: %s",
                persona.full_name,
                exc
            )

            # Fallback
            return (
                f"{persona.full_name or 'Ta osoba'} wyróżnia się w segmencie "
                f"'{segment_brief.segment_name}' swoim unikalnym podejściem do życia i pracy."
            )

    async def get_or_generate_segment_brief(
        self,
        request: SegmentBriefRequest
    ) -> SegmentBriefResponse:
        """
        Public API: Pobiera segment brief z cache lub generuje nowy.

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
        if from_cache:
            # Sprawdź TTL
            cache_key = self._get_cache_key(str(project_id), brief.segment_id)
            try:
                redis_client = get_redis_client()
                ttl = await redis_client.ttl(cache_key)
                cache_ttl_seconds = ttl if ttl > 0 else None
            except Exception:  # pragma: no cover - best effort cache probe
                cache_ttl_seconds = None
        else:
            cache_ttl_seconds = None

        return SegmentBriefResponse(
            brief=brief,
            from_cache=from_cache,
            cache_ttl_seconds=cache_ttl_seconds
        )
