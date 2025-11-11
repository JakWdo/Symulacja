"""
Persona Details Enrichment - Formatowanie i wzbogacanie danych persony

Funkcje pomocnicze do:
- Formatowania nazw segmentów i opisów
- Budowania kontekstu społecznego
- Pobierania needs & pains analysis
- Integracji z RAG i segment brief
"""

import logging
import re
import unicodedata
from typing import Any

from app.models import Persona
from app.services.personas.persona_needs_service import PersonaNeedsService
from app.services.personas.segment_brief_service import SegmentBriefService
from sqlalchemy.ext.asyncio import AsyncSession

# Import labels z config
try:
    from config import demographics
    LABELS = demographics.poland.labels
except Exception:
    # Fallback do hardcoded wartości jeśli config nie jest dostępny
    LABELS = {
        "gender": {"female": "Kobiety", "male": "Mężczyźni", "other": "Osoby", "unknown": "Osoby"},
        "segment": {"default_name": "Segment demograficzny", "age_suffix": "lat"},
        "descriptions": {
            "includes": "obejmuje",
            "age_about": "w wieku około",
            "years": "lat",
            "with_education": "z wykształceniem",
            "income_about": "osiągające dochody około",
            "distributed_poland": "rozproszone w całej Polsce",
            "living_in": "mieszkające w",
            "group_dominant": "W tej grupie dominują osoby",
            "key_characteristics": "Kluczowe wyróżniki:",
            "context_undefined": "Kontekst segmentu nie został jeszcze zdefiniowany.",
        }
    }

logger = logging.getLogger(__name__)


def _gender_label_for_persona(gender: str | None) -> str:
    if not gender:
        return LABELS.get("gender", {}).get("unknown", "Osoby")
    lowered = gender.strip().lower()
    if lowered.startswith("k"):
        return LABELS.get("gender", {}).get("female", "Kobiety")
    if lowered.startswith("m"):
        return LABELS.get("gender", {}).get("male", "Mężczyźni")
    return LABELS.get("gender", {}).get("other", "Osoby")


def _slugify_segment_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return ascii_text


def _sanitize_context_text(text: str | None, max_length: int = 900) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"[`*_#>\[\]]+", "", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    if max_length and len(cleaned) > max_length:
        truncated = cleaned[:max_length].rsplit(" ", 1)[0]
        return f"{truncated}..."
    return cleaned


def _build_segment_name_from_persona(persona: Persona) -> str:
    gender_label = _gender_label_for_persona(persona.gender)
    parts: list[str] = [gender_label]

    age_suffix = LABELS.get("segment", {}).get("age_suffix", "lat")
    if persona.age:
        parts.append(f"{persona.age} {age_suffix}")
    if persona.education_level:
        parts.append(persona.education_level)
    if persona.location and persona.location.lower() not in {"polska", "kraj"}:
        parts.append(persona.location)

    name = " ".join(part for part in parts if part).strip()
    if not name:
        name = LABELS.get("segment", {}).get("default_name", "Segment demograficzny")
    if len(name) > 60:
        name = name[:57].rstrip() + "..."
    return name


def _build_segment_description_from_persona(persona: Persona, segment_name: str) -> str:
    gender_label = _gender_label_for_persona(persona.gender)
    desc_labels = LABELS.get("descriptions", {})

    if persona.age:
        age_about = desc_labels.get("age_about", "w wieku około")
        years = desc_labels.get("years", "lat")
        subject = f"{gender_label.lower()} {age_about} {persona.age} {years}"
    else:
        subject = gender_label.lower()

    includes = desc_labels.get("includes", "obejmuje")
    sentences = [f"{segment_name} {includes} {subject}."]

    details: list[str] = []
    if persona.education_level:
        with_education = desc_labels.get("with_education", "z wykształceniem")
        details.append(f"{with_education} {persona.education_level}")
    if persona.income_bracket:
        income_about = desc_labels.get("income_about", "osiągające dochody około")
        details.append(f"{income_about} {persona.income_bracket}")
    if persona.location:
        if persona.location.lower() in {"polska", "kraj"}:
            details.append(desc_labels.get("distributed_poland", "rozproszone w całej Polsce"))
        else:
            living_in = desc_labels.get("living_in", "mieszkające w")
            details.append(f"{living_in} {persona.location}")

    if details:
        group_dominant = desc_labels.get("group_dominant", "W tej grupie dominują osoby")
        sentences.append(f"{group_dominant} {', '.join(details)}.")

    return " ".join(sentences)


def _build_segment_social_context(persona: Persona, details: dict[str, Any], fallback_description: str) -> str:
    orchestration = dict((details.get("orchestration_reasoning") or {}))
    demographics = orchestration.get("demographics") or details.get("demographics") or {
        "age": persona.age,
        "gender": persona.gender,
        "education": persona.education_level,
        "income": persona.income_bracket,
        "location": persona.location,
    }
    if not isinstance(demographics, dict):
        try:
            demographics = dict(demographics)
        except Exception:
            demographics = {
                "age": persona.age,
                "gender": persona.gender,
                "education": persona.education_level,
                "income": persona.income_bracket,
                "location": persona.location,
            }

    segment_name = (
        orchestration.get("segment_name")
        or details.get("segment_name")
        or persona.segment_name
        or _build_segment_name_from_persona(persona)
    )

    def first_sentences(text: str, limit: int = 2) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return " ".join(sentences[:limit]).strip()

    raw_characteristics = orchestration.get("segment_characteristics") or details.get("segment_characteristics") or []
    characteristics = [str(item).strip() for item in raw_characteristics if str(item).strip()]

    description = _build_segment_description_from_persona(persona, segment_name or "Segment demograficzny")
    sentences = [description]

    allocation_summary = orchestration.get("allocation_reasoning") or details.get("allocation_reasoning")
    allocation_summary = _sanitize_context_text(allocation_summary, max_length=220)
    if allocation_summary:
        sentences.append(first_sentences(allocation_summary))

    if characteristics:
        key_chars = LABELS.get("descriptions", {}).get("key_characteristics", "Kluczowe wyróżniki:")
        sentences.append(key_chars + " " + ", ".join(characteristics[:4]) + ".")

    combined = " ".join(sentences).strip()
    context_undefined = LABELS.get("descriptions", {}).get("context_undefined", "Kontekst segmentu nie został jeszcze zdefiniowany.")
    return _sanitize_context_text(combined, max_length=400) or context_undefined


def ensure_segment_metadata(persona: Persona) -> dict[str, Any] | None:
    """
    Zapewnia kompletne metadane segmentu w rag_context_details persony.

    Tworzy/uzupełnia:
    - segment_name (catchy nazwa)
    - segment_id (slug)
    - segment_description (opis demograficzny)
    - segment_social_context (kontekst społeczny)

    Args:
        persona: Obiekt Persona

    Returns:
        Dict z uzupełnionymi metadanymi lub None jeśli brak rag_context_details
    """
    details = persona.rag_context_details or {}
    if not isinstance(details, dict):
        return details

    details_copy: dict[str, Any] = dict(details)
    orchestration = dict(details_copy.get("orchestration_reasoning") or {})
    mutated = False

    existing_segment_name = orchestration.get("segment_name") or details_copy.get("segment_name")
    segment_name = persona.segment_name or existing_segment_name
    if segment_name and segment_name != existing_segment_name:
        mutated = True
    if not segment_name:
        segment_name = _build_segment_name_from_persona(persona)
        mutated = True

    existing_segment_id = orchestration.get("segment_id") or details_copy.get("segment_id")
    segment_id = persona.segment_id or existing_segment_id
    if segment_id and segment_id != existing_segment_id:
        mutated = True
    if not segment_id and segment_name:
        slug = _slugify_segment_name(segment_name)
        segment_id = slug or f"segment-{persona.id}"
        mutated = True

    segment_description = (
        orchestration.get("segment_description")
        or details_copy.get("segment_description")
    )
    if not segment_description and segment_name:
        segment_description = _build_segment_description_from_persona(persona, segment_name)
        mutated = True

    segment_social_context = (
        orchestration.get("segment_social_context")
        or details_copy.get("segment_social_context")
    )
    computed_social_context = _build_segment_social_context(persona, details_copy, segment_description or "")
    if computed_social_context and computed_social_context != segment_social_context:
        segment_social_context = computed_social_context
        mutated = True
    elif not segment_social_context and computed_social_context:
        segment_social_context = computed_social_context
        mutated = True

    if mutated:
        if segment_name:
            orchestration["segment_name"] = segment_name
            details_copy["segment_name"] = segment_name
        if segment_id:
            orchestration["segment_id"] = segment_id
            details_copy["segment_id"] = segment_id
        if segment_description:
            orchestration["segment_description"] = segment_description
            details_copy["segment_description"] = segment_description
        if segment_social_context:
            orchestration["segment_social_context"] = segment_social_context
            details_copy["segment_social_context"] = segment_social_context

    details_copy["orchestration_reasoning"] = orchestration
    return details_copy


async def fetch_needs_and_pains(
    db: AsyncSession,
    persona: Persona,
    *,
    force_refresh: bool,
) -> dict[str, Any] | None:
    """
    Fetch needs & pains analysis from cache or generate via LLM with RAG context.

    Args:
        db: AsyncSession
        persona: Persona object
        force_refresh: Whether to bypass cache

    Returns:
        Dict with JTBD, desired outcomes, and pain points

    Performance:
        - Cache hit: < 10ms (return persona.needs_and_pains)
        - Cache miss: < 2s (LLM with structured output + RAG context)
    """
    service = PersonaNeedsService(db)
    try:
        if persona.needs_and_pains and not force_refresh:
            return persona.needs_and_pains

        # Extract RAG context for consistency with segment data
        rag_context = extract_rag_context(persona)

        # Generate needs with RAG context
        needs_data = await service.generate_needs_analysis(persona, rag_context=rag_context)
        return needs_data
    except Exception as exc:
        logger.error("Failed to generate needs for persona %s: %s", persona.id, exc, exc_info=True)
        return persona.needs_and_pains


def extract_rag_context(persona: Persona) -> str | None:
    """
    Ekstrahuje RAG context z rag_context_details persony.

    Priorytet:
    1. segment_social_context (z orchestration_reasoning)
    2. overall_context (z orchestration_reasoning)
    3. graph_context (z rag_context_details)

    Args:
        persona: Obiekt Persona

    Returns:
        RAG context string lub None jeśli brak kontekstu
    """
    details = persona.rag_context_details or {}
    reasoning = details.get("orchestration_reasoning") or {}
    context_candidates = [
        reasoning.get("segment_social_context"),
        reasoning.get("overall_context"),
        details.get("graph_context"),
    ]
    for candidate in context_candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


async def fetch_segment_brief(
    db: AsyncSession,
    persona: Persona,
    *,
    force_refresh: bool,
) -> dict[str, Any] | None:
    """
    Fetch segment brief i persona uniqueness używając SegmentBriefService.

    Args:
        db: AsyncSession
        persona: Persona object
        force_refresh: Whether to bypass cache

    Returns:
        Dict z segment_brief i persona_uniqueness lub None jeśli failuje

    Performance:
        - Cache hit (segment brief): < 50ms
        - Cache miss: < 5s (RAG + LLM dla briefu + uniqueness)
    """
    try:
        segment_service = SegmentBriefService(db)

        # Przygotuj demographics z persony
        demographics = {
            "age": persona.age or "unknown",
            "gender": persona.gender or "unknown",
            "education": persona.education_level or "unknown",
            "location": persona.location or "unknown",
            "income": persona.income_bracket or "unknown",
        }

        # Generuj/pobierz segment brief (z cache jeśli !force_refresh)
        segment_brief = await segment_service.generate_segment_brief(
            demographics=demographics,
            project_id=persona.project_id,
            max_example_personas=3,
            force_refresh=force_refresh
        )

        # Generuj persona uniqueness
        persona_uniqueness = await segment_service.generate_persona_uniqueness(
            persona=persona,
            segment_brief=segment_brief
        )

        logger.info(
            "✅ Segment brief fetched for persona %s (segment: %s, from_cache: %s)",
            persona.id,
            segment_brief.segment_id,
            not force_refresh
        )

        return {
            "segment_brief": segment_brief.model_dump(mode="json"),
            "persona_uniqueness": persona_uniqueness,
        }

    except Exception as exc:
        logger.error(
            "Failed to generate segment brief for persona %s: %s",
            persona.id,
            exc,
            exc_info=True
        )
        return None
