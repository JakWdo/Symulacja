"""
API Endpoints - Zarządzanie Personami

Endpointy do generowania i zarządzania syntetycznymi personami dla badań rynkowych.

Główne funkcjonalności:
- POST /projects/{project_id}/personas/generate - generuje persony z AI (async background task)
- GET /projects/{project_id}/personas - pobiera wszystkie persony projektu
- GET /personas/{persona_id} - pobiera szczegóły pojedynczej persony
- DELETE /personas/{persona_id} - usuwa personę (soft delete)

Generowanie person:
1. Parsuje rozkłady demograficzne z target_demographics projektu
2. Uruchamia PersonaGenerator (Google Gemini Flash) w tle
3. Waliduje statystycznie wygenerowane persony (chi-kwadrat)
4. Zapisuje do bazy danych
5. Czas: ~1.5-3s per persona, ~30-60s dla 20 person

Używa background tasks - endpoint zwraca 202 Accepted natychmiast.
"""

import asyncio
import json
import logging
import random
import re
import unicodedata
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, get_db
from app.models import Project, Persona, User
from app.services.personas.persona_orchestration import PersonaOrchestrationService
from app.api.dependencies import get_current_user, get_project_for_user, get_persona_for_user
from app.schemas.persona import (
    PersonaResponse,
    PersonaGenerateRequest,
    PersonaReasoningResponse,
    GraphInsightResponse,
)
from app.schemas.persona_details import (
    PersonaDetailsResponse,
    PersonaExportRequest,
    PersonaExportResponse,
    PersonaDeleteRequest,
    PersonaDeleteResponse,
    PersonaUndoDeleteResponse,
    PersonaMessagingRequest,
    PersonaMessagingResponse,
    PersonaComparisonRequest,
    PersonaComparisonResponse,
)
from app.services import DemographicDistribution
from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain as PreferredPersonaGenerator
from app.services.personas.persona_validator import PersonaValidator
from app.services.personas.persona_details_service import PersonaDetailsService
from app.services.personas.persona_audit_service import PersonaAuditService
from app.services.personas.persona_messaging_service import PersonaMessagingService
from app.services.personas.persona_comparison_service import PersonaComparisonService
from app.services.personas.persona_narrative_service import PersonaNarrativeService
from app.core.constants import (
    # Używane tylko do utility (normalizacja, translacja)
    POLISH_LOCATIONS,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

# Śledź uruchomione zadania aby zapobiec garbage collection
_running_tasks = set()


def _graph_node_to_insight_response(node: Dict[str, Any]) -> Optional[GraphInsightResponse]:
    """Konwertuje surowy węzeł grafu (Neo4j) na GraphInsightResponse."""
    if not node:
        return None

    summary = node.get("summary") or node.get("streszczenie")
    if not summary:
        return None

    magnitude = node.get("magnitude") or node.get("skala")
    confidence_raw = node.get("confidence") or node.get("pewnosc") or node.get("pewność")
    confidence_map = {
        "wysoka": "high",
        "średnia": "medium",
        "srednia": "medium",
        "niska": "low",
    }
    if isinstance(confidence_raw, str):
        confidence = confidence_map.get(confidence_raw.lower(), confidence_raw.lower())
    else:
        confidence = "medium"

    time_period = node.get("time_period") or node.get("okres_czasu")
    source = (
        node.get("source")
        or node.get("document_title")
        or node.get("Źródło")
        or node.get("źródło")
    )

    why_matters = (
        node.get("why_matters")
        or node.get("kluczowe_fakty")
        or node.get("explanation")
        or summary
    )

    try:
        return GraphInsightResponse(
            type=node.get("type", "Insight"),
            summary=summary,
            magnitude=magnitude,
            confidence=confidence or "medium",
            time_period=time_period,
            source=source,
            why_matters=why_matters,
        )
    except Exception as exc:  # pragma: no cover - graceful fallback
        logger.warning("Failed to convert graph node to insight: %s", exc)
        return None


@lru_cache(maxsize=1)
def _get_persona_generator() -> PreferredPersonaGenerator:
    logger.info("Initializing cached persona generator instance")
    return PreferredPersonaGenerator()


def _calculate_concurrency_limit(num_personas: int, adversarial_mode: bool) -> int:
    base_limit = max(3, min(12, (num_personas // 3) + 3))
    if adversarial_mode:
        base_limit = max(2, base_limit - 2)
    if num_personas > 0:
        base_limit = min(base_limit, num_personas)
    return base_limit


_NAME_FROM_STORY_PATTERN = re.compile(
    r"^(?P<name>[A-Z][a-z]+(?: [A-Z][a-z]+){0,2})\s+is\s+(?:an|a)\s",
)
_AGE_IN_STORY_PATTERN = re.compile(r"(?P<age>\d{1,3})-year-old")
# Wzorce do ekstrakcji wieku z polskiego tekstu
# WAŻNE: Negative lookahead (?!\s+doświadczenia) zapobiega matchowaniu "10 lat doświadczenia"
_POLISH_AGE_PATTERNS = [
    re.compile(r"(?:ma|mam)\s+(?P<age>\d{1,2})\s+lat(?!\s+doświadczenia)", re.IGNORECASE),  # "ma 32 lata" ale NIE "ma 10 lat doświadczenia"
    re.compile(r"(?P<age>\d{1,2})-letni[aey]?(?!\s+doświadczeni)", re.IGNORECASE),  # "32-letnia" ale NIE "10-letni doświadczeniem"
    re.compile(r"(?P<age>\d{1,2})\s+lat(?!\s+(?:doświadczenia|pracy|stażu|w))", re.IGNORECASE),  # "32 lat" ale NIE "10 lat doświadczenia/pracy/stażu/w firmie"
]


# Mapowania i pomocnicze słowniki dla polonizacji danych
_POLISH_CHARACTERS = set("ąćęłńóśźż")
_POLISH_CITY_LOOKUP = {
    # Normalizujemy nazwy miast aby móc dopasować różne warianty zapisu
    "".join(ch for ch in unicodedata.normalize("NFD", city) if not unicodedata.combining(ch)).lower(): city
    for city in POLISH_LOCATIONS.keys()
}

_EN_TO_PL_GENDER = {
    "female": "Kobieta",
    "kobieta": "Kobieta",
    "male": "Mężczyzna",
    "mężczyzna": "Mężczyzna",
    "man": "Mężczyzna",
    "woman": "Kobieta",
    "non-binary": "Osoba niebinarna",
    "nonbinary": "Osoba niebinarna",
    "other": "Osoba niebinarna",
}

_EN_TO_PL_EDUCATION = {
    "high school": "Średnie ogólnokształcące",
    "some college": "Policealne",
    "bachelor's degree": "Wyższe licencjackie",
    "masters degree": "Wyższe magisterskie",
    "master's degree": "Wyższe magisterskie",
    "doctorate": "Doktorat",
    "phd": "Doktorat",
    "technical school": "Średnie techniczne",
    "trade school": "Zasadnicze zawodowe",
    "vocational": "Zasadnicze zawodowe",
}

_EN_TO_PL_INCOME = {
    "< $25k": "< 3 000 zł",
    "$25k-$50k": "3 000 - 5 000 zł",
    "$50k-$75k": "5 000 - 7 500 zł",
    "$75k-$100k": "7 500 - 10 000 zł",
    "$100k-$150k": "10 000 - 15 000 zł",
    "> $150k": "> 15 000 zł",
    "$150k+": "> 15 000 zł",
}

_ADDITIONAL_CITY_ALIASES = {
    "warsaw": "Warszawa",
    "krakow": "Kraków",
    "wroclaw": "Wrocław",
    "poznan": "Poznań",
    "lodz": "Łódź",
    "gdansk": "Gdańsk",
    "gdynia": "Gdynia",
    "szczecin": "Szczecin",
    "lublin": "Lublin",
    "bialystok": "Białystok",
    "bydgoszcz": "Bydgoszcz",
    "katowice": "Katowice",
    "czestochowa": "Częstochowa",
    "torun": "Toruń",
    "radom": "Radom",
}


def _normalize_text(value: Optional[str]) -> str:
    """Usuń diakrytyki i sprowadź tekst do małych liter – pomocne przy dopasowaniach."""
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.lower().strip()


def _select_weighted(distribution: Dict[str, float]) -> Optional[str]:
    """Wybierz losowy element z podanego rozkładu prawdopodobieństwa."""
    if not distribution:
        return None
    options = list(distribution.keys())
    weights = list(distribution.values())
    return random.choices(options, weights=weights, k=1)[0]


def _extract_polish_location_from_story(story: Optional[str]) -> Optional[str]:
    """Spróbuj znaleźć polską lokalizację wewnątrz historii tła persony."""
    if not story:
        return None
    normalized_story = _normalize_text(story)
    for normalized_city, original_city in _POLISH_CITY_LOOKUP.items():
        if normalized_city and normalized_city in normalized_story:
            return original_city
        # Obsługa odmian fleksyjnych (np. Wrocławiu, Gdańsku)
        if normalized_city.endswith("a") and normalized_city + "ch" in normalized_story:
            return original_city
        if normalized_city + "iu" in normalized_story or normalized_city + "u" in normalized_story:
            return original_city
        if normalized_city + "ie" in normalized_story:
            return original_city
    return None


def _ensure_polish_location(location: Optional[str], story: Optional[str]) -> str:
    """Zadbaj aby lokalizacja była polska – użyj historii lub losowania z listy."""
    normalized = _normalize_text(location)
    if normalized:
        if normalized in _POLISH_CITY_LOOKUP:
            return _POLISH_CITY_LOOKUP[normalized]
        if normalized in _ADDITIONAL_CITY_ALIASES:
            return _ADDITIONAL_CITY_ALIASES[normalized]
        # Usuń przyrostki typu ", ca" itp.
        stripped_parts = re.split(r"[,/\\]", normalized)
        for part in stripped_parts:
            part = part.strip()
            if part in _POLISH_CITY_LOOKUP:
                return _POLISH_CITY_LOOKUP[part]
            if part in _ADDITIONAL_CITY_ALIASES:
                return _ADDITIONAL_CITY_ALIASES[part]
    story_city = _extract_polish_location_from_story(story)
    if story_city:
        return story_city
    fallback = _select_weighted(POLISH_LOCATIONS) or "Warszawa"
    return fallback


def _polishify_gender(raw_gender: Optional[str]) -> str:
    """Przekonwertuj nazwy płci na polskie odpowiedniki."""
    normalized = _normalize_text(raw_gender)
    return _EN_TO_PL_GENDER.get(normalized, raw_gender.title() if raw_gender else "Kobieta")


def _polishify_education(raw_education: Optional[str]) -> str:
    """Przekonwertuj poziom wykształcenia na polską etykietę."""
    normalized = _normalize_text(raw_education)
    if normalized in _EN_TO_PL_EDUCATION:
        return _EN_TO_PL_EDUCATION[normalized]
    if raw_education:
        return raw_education
    return _select_weighted(POLISH_EDUCATION_LEVELS) or "Średnie ogólnokształcące"


def _polishify_income(raw_income: Optional[str]) -> str:
    """Przekonwertuj przedział dochodowy na złotówki."""
    normalized = raw_income.strip() if isinstance(raw_income, str) else None
    if normalized:
        normalized_key = normalized.replace(" ", "")
        if normalized in _EN_TO_PL_INCOME:
            return _EN_TO_PL_INCOME[normalized]
        if normalized_key in _EN_TO_PL_INCOME:
            return _EN_TO_PL_INCOME[normalized_key]
    return raw_income if raw_income else (_select_weighted(POLISH_INCOME_BRACKETS) or "5 000 - 7 500 zł")


_SEGMENT_GENDER_LABELS = {
    "kobieta": "Kobiety",
    "kobiety": "Kobiety",
    "female": "Kobiety",
    "mężczyzna": "Mężczyźni",
    "mezczyzna": "Mężczyźni",
    "mężczyzni": "Mężczyźni",
    "mężczyźni": "Mężczyźni",
    "male": "Mężczyźni",
}


def _segment_gender_label(raw_gender: Optional[str]) -> str:
    normalized = _normalize_text(raw_gender)
    return _SEGMENT_GENDER_LABELS.get(normalized, "Osoby")


def _format_age_segment(raw_age: Optional[str]) -> Optional[str]:
    if raw_age is None:
        return None
    age_str = str(raw_age).strip()
    if not age_str:
        return None
    if age_str.replace("+", "").isdigit() or "-" in age_str:
        if age_str.endswith("lat"):
            return age_str
        return f"{age_str} lat"
    return age_str


def _format_education_phrase(raw_education: Optional[str]) -> Optional[str]:
    if not raw_education:
        return None
    value = str(raw_education).strip()
    lower = value.lower()
    if "wyższ" in lower:
        return "z wyższym wykształceniem"
    if "średn" in lower:
        return "ze średnim wykształceniem"
    if "zawod" in lower:
        return "z wykształceniem zawodowym"
    if "podstaw" in lower:
        return "z wykształceniem podstawowym"
    if value:
        return f"z wykształceniem {value}"
    return None


def _format_income_phrase(raw_income: Optional[str]) -> Optional[str]:
    if not raw_income:
        return None
    value = str(raw_income).strip()
    if not value:
        return None
    if any(char.isdigit() for char in value):
        return f"osiągające dochody około {value}"
    return f"o dochodach {value}"


def _format_location_phrase(raw_location: Optional[str]) -> Optional[str]:
    if not raw_location:
        return None
    value = str(raw_location).strip()
    if not value:
        return None
    normalized = _normalize_text(value)
    if normalized in {"polska", "kraj", "calapolska", "całapolska", "cała polska"}:
        return "rozproszone w całej Polsce"
    return f"mieszkające w {value}"


def _slugify_segment(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return ascii_text


def _sanitize_brief_text(text: Optional[str], max_length: int = 900) -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"[`*_#>\[\]]+", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    if max_length and len(cleaned) > max_length:
        truncated = cleaned[:max_length].rsplit(" ", 1)[0]
        return f"{truncated}..."
    return cleaned


def _segment_subject_descriptor(gender_label: str, age_phrase: Optional[str]) -> str:
    base = gender_label.lower() if gender_label and gender_label != "Osoby" else "osoby"
    if age_phrase:
        return f"{base} w wieku {age_phrase}"
    return base


def _compose_segment_description(
    demographics: Dict[str, Any],
    segment_name: str,
) -> str:
    gender_label = _segment_gender_label(demographics.get("gender"))
    age_phrase = _format_age_segment(demographics.get("age") or demographics.get("age_group"))
    education_phrase = _format_education_phrase(
        demographics.get("education") or demographics.get("education_level")
    )
    income_phrase = _format_income_phrase(
        demographics.get("income") or demographics.get("income_bracket")
    )
    location_phrase = _format_location_phrase(demographics.get("location"))

    subject = _segment_subject_descriptor(gender_label, age_phrase)
    segment_label = segment_name or "Ten segment"

    sentences = [f"{segment_label} obejmuje {subject}."]
    details = [phrase for phrase in [education_phrase, income_phrase, location_phrase] if phrase]
    if details:
        detail_sentence = ", ".join(details)
        sentences.append(f"W tej grupie dominują osoby {detail_sentence}.")

    return " ".join(sentences)


def _compose_segment_name(
    demographics: Dict[str, Any],
    group_index: int,
) -> str:
    gender_label = _segment_gender_label(demographics.get("gender"))
    age_value = demographics.get("age") or demographics.get("age_group")
    location = demographics.get("location")
    education_raw = demographics.get("education") or demographics.get("education_level")

    age_component = None
    if age_value:
        age_component = str(age_value).replace("lat", "").strip()

    education_component = None
    if education_raw:
        value = str(education_raw).strip()
        lower = value.lower()
        if "wyższ" in lower:
            education_component = "wyższe wykształcenie"
        elif "średn" in lower:
            education_component = "średnie wykształcenie"
        elif "zawod" in lower:
            education_component = "zawodowe wykształcenie"

    location_component = None
    if location:
        normalized_loc = _normalize_text(location)
        if normalized_loc not in {"polska", "kraj", "calapolska", "całapolska"}:
            location_component = str(location).strip()

    parts = []
    if gender_label and gender_label != "Osoby":
        parts.append(gender_label)
    else:
        parts.append("Osoby")
    if age_component:
        parts.append(age_component)
    if education_component:
        parts.append(education_component)
    if location_component:
        parts.append(location_component)

    name = " ".join(parts).strip()
    if not name:
        name = f"Segment {group_index + 1}"
    if len(name) > 60:
        name = name[:57].rstrip() + "..."
    return name


def _build_segment_metadata(
    demographics: Dict[str, Any],
    brief: Optional[str],
    allocation_reasoning: Optional[str],
    group_index: int,
) -> Dict[str, Optional[str]]:
    segment_name = _compose_segment_name(demographics, group_index)
    slug = _slugify_segment(segment_name)
    if not slug:
        slug = f"segment-{group_index + 1}"

    description = _compose_segment_description(demographics, segment_name)
    social_context = _sanitize_brief_text(brief)
    if not social_context:
        social_context = _sanitize_brief_text(allocation_reasoning)
    if not social_context:
        social_context = description

    return {
        "segment_name": segment_name,
        "segment_id": slug,
        "segment_description": description,
        "segment_social_context": social_context,
    }


def _looks_polish_phrase(text: Optional[str]) -> bool:
    """Sprawdź heurystycznie czy tekst wygląda na polski (znaki diakrytyczne, słowa kluczowe)."""
    if not text:
        return False
    lowered = text.strip().lower()
    if any(char in text for char in _POLISH_CHARACTERS):
        return True
    keywords = ["specjalista", "menedżer", "koordynator", "student", "uczeń", "właściciel", "kierownik", "logistyk"]
    return any(keyword in lowered for keyword in keywords)


def _format_job_title(job: str) -> str:
    """Ujednolicenie formatowania tytułu zawodowego."""
    job = job.strip()
    if not job:
        return job
    return job[0].upper() + job[1:]


_BACKGROUND_JOB_PATTERNS = [
    re.compile(r"pracuje jako (?P<job>[^\.,]+)", re.IGNORECASE),
    re.compile(r"jest (?P<job>[^\.,]+) w", re.IGNORECASE),
    re.compile(r"na stanowisku (?P<job>[^\.,]+)", re.IGNORECASE),
    re.compile(r"pełni funkcję (?P<job>[^\.,]+)", re.IGNORECASE),
]


def _infer_polish_occupation(
    education_level: Optional[str],
    income_bracket: Optional[str],
    age: int,
    personality: Dict[str, Any],
    background_story: Optional[str],
) -> str:
    """
    Ustal możliwie polski tytuł zawodowy bazując na dostępnych danych.

    Zawód MUSI być generowany przez LLM (w orchestration brief).
    Ta funkcja tylko ekstraktuje go z personality lub background_story.
    """
    # Preferuj persona_title (wygenerowane przez LLM)
    candidate = personality.get("persona_title") or personality.get("occupation")
    if candidate and _looks_polish_phrase(candidate):
        return _format_job_title(candidate)

    # Spróbuj wyekstraktować z background_story
    if background_story:
        for pattern in _BACKGROUND_JOB_PATTERNS:
            match = pattern.search(background_story)
            if match:
                job = match.group("job").strip()
                if job:
                    return _format_job_title(job)

    # OSTATNIA LINIA OBRONY: jeśli LLM całkowicie zawiódł
    # (nie powinno się zdarzyć jeśli orchestration brief był dobry)
    logger.error(f"❌ LLM failed to generate occupation - no occupation found in personality or background_story")
    return "Specjalista"  # Generyczny fallback


def _fallback_polish_list(source: Optional[List[str]], fallback_pool: List[str]) -> List[str]:
    """Zapewnij, że listy wartości i zainteresowań mają polskie elementy."""
    if source:
        return [item for item in source if isinstance(item, str) and item.strip()]
    if not fallback_pool:
        return []
    sample_size = min(5, len(fallback_pool))
    return random.sample(fallback_pool, k=sample_size)


def _infer_full_name(background_story: Optional[str]) -> Optional[str]:
    if not background_story:
        return None
    match = _NAME_FROM_STORY_PATTERN.match(background_story.strip())
    if match:
        return match.group('name')
    return None


def _extract_age_from_story(background_story: Optional[str]) -> Optional[int]:
    """
    Ekstraktuj wiek z background_story (wspiera polski i angielski tekst)

    Args:
        background_story: Historia życiowa persony

    Returns:
        Wyekstraktowany wiek lub None jeśli nie znaleziono
    """
    if not background_story:
        return None

    # Spróbuj angielski wzorzec "32-year-old"
    match = _AGE_IN_STORY_PATTERN.search(background_story)
    if match:
        try:
            return int(match.group('age'))
        except (ValueError, AttributeError):
            pass

    # Spróbuj polskie wzorce
    for pattern in _POLISH_AGE_PATTERNS:
        match = pattern.search(background_story)
        if match:
            try:
                age = int(match.group('age'))
                if 10 <= age <= 100:  # Sanity check
                    return age
            except (ValueError, AttributeError):
                continue

    return None


def _fallback_full_name(gender: Optional[str], age: int) -> str:
    gender_label = (gender or "Persona").split()[0].capitalize()
    return f"{gender_label} {age}"


def _compose_headline(
    full_name: str,
    persona_title: Optional[str],
    occupation: Optional[str],
    location: Optional[str],
) -> str:
    primary_role = persona_title or occupation
    name_root = full_name.split()[0]
    if primary_role and location:
        return f"{primary_role} based in {location}"
    if primary_role:
        return primary_role
    if location:
        return f"{name_root} from {location}"
    return f"{name_root}'s persona profile"


def _get_consistent_occupation(
    education_level: Optional[str],
    income_bracket: Optional[str],
    age: int,
    personality: Dict[str, Any],
    background_story: Optional[str],
) -> str:
    """Zapewnij polski, spójny zawód bazując na danych kontekstowych."""
    return _infer_polish_occupation(education_level, income_bracket, age, personality, background_story)


def _ensure_story_alignment(
    story: Optional[str],
    age: int,
    occupation: Optional[str],
) -> Optional[str]:
    if not story:
        return story
    text = story.strip()
    match = _AGE_IN_STORY_PATTERN.search(text)
    if match and match.group('age') != str(age):
        text = _AGE_IN_STORY_PATTERN.sub(f"{age}-year-old", text, count=1)
    return text


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(value for value in weights.values() if value > 0)
    if total <= 0:
        return weights
    return {key: value / total for key, value in weights.items() if value > 0}


def _coerce_distribution(raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    if not raw:
        return None
    cleaned: Dict[str, float] = {}
    for key, value in raw.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0:
            cleaned[str(key)] = numeric
    return _normalize_weights(cleaned) if cleaned else None


def _age_group_bounds(label: str) -> Tuple[int, Optional[int]]:
    if '-' in label:
        start, end = label.split('-', maxsplit=1)
        try:
            return int(start), int(end)
        except ValueError:
            return 0, None
    if label.endswith('+'):
        try:
            base = int(label.rstrip('+'))
            return base, None
        except ValueError:
            return 0, None
    try:
        value = int(label)
        return value, value
    except ValueError:
        return 0, None


def _age_group_overlaps(label: str, min_age: Optional[int], max_age: Optional[int]) -> bool:
    group_min, group_max = _age_group_bounds(label)
    if min_age is not None and group_max is not None and group_max < min_age:
        return False
    if max_age is not None and group_min is not None and group_min > max_age:
        return False
    return True


def _apply_age_preferences(
    age_groups: Dict[str, float],
    focus: Optional[str],
    min_age: Optional[int],
    max_age: Optional[int],
) -> Dict[str, float]:
    adjusted = {
        label: weight
        for label, weight in age_groups.items()
        if _age_group_overlaps(label, min_age, max_age)
    }
    if not adjusted:
        adjusted = dict(age_groups)

    if focus == 'young_adults':
        for label in adjusted:
            lower, upper = _age_group_bounds(label)
            upper_value = upper if upper is not None else lower + 5
            if upper_value <= 35:
                adjusted[label] *= 1.8
            else:
                adjusted[label] *= 0.6
    elif focus == 'experienced_leaders':
        for label in adjusted:
            lower, _ = _age_group_bounds(label)
            if lower >= 35:
                adjusted[label] *= 1.8
            else:
                adjusted[label] *= 0.6

    normalized = _normalize_weights(adjusted)
    return normalized if normalized else dict(age_groups)


def _apply_gender_preferences(genders: Dict[str, float], balance: Optional[str]) -> Dict[str, float]:
    if balance == 'female_skew':
        return _normalize_weights({
            'female': 0.65,
            'male': 0.3,
            'non-binary': 0.05,
        })
    if balance == 'male_skew':
        return _normalize_weights({
            'male': 0.65,
            'female': 0.3,
            'non-binary': 0.05,
        })
    return genders


def _build_location_distribution(
    base_locations: Dict[str, float],
    advanced_options: Optional[Dict[str, Any]],
) -> Dict[str, float]:
    if not advanced_options:
        return base_locations

    cities = advanced_options.get('target_cities') or []
    countries = advanced_options.get('target_countries') or []

    if cities:
        city_weights = {city: 1 / len(cities) for city in cities}
        return _normalize_weights(city_weights)

    if countries:
        country_weights = {country: 1 / len(countries) for country in countries}
        return _normalize_weights(country_weights)

    urbanicity = advanced_options.get('urbanicity')
    if urbanicity == 'urban':
        return base_locations
    if urbanicity == 'suburban':
        return {}
    if urbanicity == 'rural':
        return {}

    return base_locations


def _create_simple_fallback_allocation(
    num_personas: int,
    target_demographics: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Tworzy prosty fallback plan alokacji gdy orchestration service failuje.

    Dystrybuuje persony równomiernie między główne grupy demograficzne
    z target_demographics projektu. Briefe są krótkie i generyczne (bez Graph insights).

    Args:
        num_personas: Liczba person do wygenerowania
        target_demographics: Target demographics projektu (age_group, gender, education_level, location)

    Returns:
        Dict z fallback allocation plan (kompatybilny z orchestration plan format)
    """
    logger.warning("🔧 Creating FALLBACK allocation plan (orchestration unavailable)")

    # Ekstraktuj główne grupy z target_demographics
    age_groups = list(target_demographics.get("age_group", {}).keys())
    genders = list(target_demographics.get("gender", {}).keys())
    education_levels = list(target_demographics.get("education_level", {}).keys())
    locations = list(target_demographics.get("location", {}).keys())

    # Fallback defaults jeśli target_demographics pusty
    if not age_groups:
        age_groups = ["25-34", "35-44"]
    if not genders:
        genders = ["kobieta", "mężczyzna"]
    if not education_levels:
        education_levels = ["wyższe"]
    if not locations:
        locations = ["Warszawa"]

    # Oblicz liczbę grup (max 4 dla prostoty)
    num_groups = min(4, num_personas)

    # Dystrybuuj persony równomiernie
    base_count = num_personas // num_groups
    remainder = num_personas % num_groups

    groups = []
    for i in range(num_groups):
        # Assign count (dodaj remainder do pierwszych grup)
        count = base_count + (1 if i < remainder else 0)

        # Wybierz demographics (cyklicznie z dostępnych wartości)
        demographics = {
            "age": age_groups[i % len(age_groups)],
            "gender": genders[i % len(genders)],
            "education": education_levels[i % len(education_levels)],
            "location": locations[i % len(locations)],
        }

        # Krótki generyczny brief (brak Graph insights w fallback)
        brief = (
            f"Grupa {i+1}: {demographics['gender']} w wieku {demographics['age']}, "
            f"wykształcenie {demographics['education']}, lokalizacja {demographics['location']}. "
            f"Segment wybrany na podstawie demografii projektu dla zróżnicowanej reprezentacji."
        )

        # Segment characteristics (generic)
        segment_characteristics = [
            f"{demographics['gender'].capitalize()} {demographics['age']} lat",
            f"Wykształcenie {demographics['education']}",
            f"Mieszkańcy: {demographics['location']}"
        ]

        # Allocation reasoning (krótki generic)
        allocation_reasoning = f"Alokacja {count} person dla reprezentacji grupy {demographics['age']}, {demographics['gender']}."

        groups.append({
            "count": count,
            "demographics": demographics,
            "brief": brief,
            "segment_characteristics": segment_characteristics,
            "allocation_reasoning": allocation_reasoning,
            "graph_insights": [],  # Brak Graph insights w fallback
        })

    fallback_plan = {
        "total_personas": num_personas,
        "overall_context": "Plan alokacji utworzony automatycznie na podstawie demografii projektu (orchestration service niedostępny).",
        "groups": groups,
    }

    logger.info(
        f"✅ Fallback allocation created: {num_groups} groups, {num_personas} personas"
    )

    return fallback_plan


def _normalize_distribution(
    distribution: Dict[str, float], fallback: Dict[str, float]
) -> Dict[str, float]:
    """Normalize distribution to sum to 1.0, or use fallback if invalid."""
    if not distribution:
        return fallback
    total = sum(distribution.values())
    if total <= 0:
        return fallback
    return {key: value / total for key, value in distribution.items()}


# DEFAULT distributions - fallback gdy target_demographics pusty
# NOTE: Demographics są GENEROWANE przez LLM z orchestration, te są tylko fallback
DEFAULT_AGE_GROUPS = {
    "18-24": 0.15,
    "25-34": 0.30,
    "35-44": 0.25,
    "45-54": 0.20,
    "55+": 0.10,
}

DEFAULT_GENDERS = {
    "female": 0.50,
    "male": 0.48,
    "non-binary": 0.02,
}


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

    # Zwróć natychmiast (nie czekaj na zakończenie generowania)
    return {
        "message": "Persona generation started in background",
        "project_id": str(project_id),
        "num_personas": generate_request.num_personas,
        "adversarial_mode": generate_request.adversarial_mode,
    }


async def _generate_personas_task(
    project_id: UUID,
    num_personas: int,
    adversarial_mode: bool,
    advanced_options: Optional[Dict[str, Any]] = None,
    use_rag: bool = True,
):
    """
    Asynchroniczne zadanie w tle do generowania person

    To zadanie wykonuje się poza cyklem request-response HTTP:
    1. Tworzy własną sesję DB (AsyncSessionLocal)
    2. Ładuje projekt i jego target_demographics
    3. Generuje persony używając PersonaGeneratorLangChain
    4. Waliduje różnorodność person
    5. Zapisuje w bazie danych
    6. Aktualizuje statystyki projektu

    WAŻNE: To zadanie NIE może używać sesji DB z HTTP requesta!
    Musi stworzyć własną sesję przez AsyncSessionLocal().

    Args:
        project_id: UUID projektu
        num_personas: Liczba person do wygenerowania
        adversarial_mode: Czy użyć adversarial prompting (dla edge cases)
        advanced_options: Opcjonalne zaawansowane opcje (custom distributions, etc.)
    """
    logger.info(f"Starting persona generation task for project {project_id}, num_personas={num_personas}")

    try:
        # Utwórz własną sesję DB (niezależną od HTTP requesta)
        async with AsyncSessionLocal() as db:
            # Generator trzymamy w cache, żeby uniknąć kosztownej inicjalizacji przy każdym zadaniu
            generator = _get_persona_generator()
            generator_name = getattr(generator, "__class__", type(generator)).__name__
            logger.info("Using %s persona generator", generator_name, extra={"project_id": str(project_id)})

            project = await db.get(Project, project_id)
            if not project:
                logger.error("Project not found in background task.", extra={"project_id": str(project_id)})
                return

            target_demographics = project.target_demographics or {}
            distribution = DemographicDistribution(
                age_groups=_normalize_distribution(target_demographics.get("age_group", {}), DEFAULT_AGE_GROUPS),
                genders=_normalize_distribution(target_demographics.get("gender", {}), DEFAULT_GENDERS),
                # Używaj POLSKICH wartości domyślnych dla lepszej realistyczności
                education_levels=_normalize_distribution(target_demographics.get("education_level", {}), POLISH_EDUCATION_LEVELS),
                income_brackets=_normalize_distribution(target_demographics.get("income_bracket", {}), POLISH_INCOME_BRACKETS),
                locations=_normalize_distribution(target_demographics.get("location", {}), POLISH_LOCATIONS),
            )

            # === ORCHESTRATION STEP (GEMINI 2.5 PRO) ===
            # Tworzymy szczegółowy plan alokacji używając orchestration agent
            orchestration_service = PersonaOrchestrationService()
            allocation_plan = None
            persona_group_mapping = {}  # Mapuje persona index -> brief

            logger.info("🎯 Creating orchestration plan with Gemini 2.5 Pro...")
            try:
                # Pobierz dodatkowy opis grupy docelowej jeśli istnieje
                target_audience_desc = None
                if advanced_options and "target_audience_description" in advanced_options:
                    target_audience_desc = advanced_options["target_audience_description"]

                # Tworzymy plan alokacji (długie briefe dla każdej grupy)
                allocation_plan = await orchestration_service.create_persona_allocation_plan(
                    target_demographics=target_demographics,
                    num_personas=num_personas,
                    project_description=project.description,
                    additional_context=target_audience_desc,
                )

                logger.info(
                    f"✅ Orchestration plan created: {len(allocation_plan.groups)} demographic groups, "
                    f"overall_context={len(allocation_plan.overall_context)} chars"
                )

                # Mapuj briefe do każdej persony
                # Strategia: Każda grupa ma `count` person, więc przydzielamy briefe sekwencyjnie
                persona_index = 0
                group_metadata: List[Dict[str, Optional[str]]] = []
                for group_index, group in enumerate(allocation_plan.groups):
                    demographics = (
                        group.demographics
                        if isinstance(group.demographics, dict)
                        else dict(group.demographics)
                    )
                    segment_metadata = _build_segment_metadata(
                        demographics,
                        group.brief,
                        group.allocation_reasoning,
                        group_index,
                    )
                    group_metadata.append(segment_metadata)
                    group_count = group.count
                    for _ in range(group_count):
                        if persona_index < num_personas:
                            persona_group_mapping[persona_index] = {
                                "brief": group.brief,
                                "graph_insights": [insight.model_dump() for insight in group.graph_insights],
                                "allocation_reasoning": group.allocation_reasoning,
                                "demographics": demographics,
                                "segment_characteristics": group.segment_characteristics,
                                **segment_metadata,
                            }
                            persona_index += 1

                # KOREKCJA: Jeśli LLM alokował za mało, dolicz brakujące do ostatniej grupy
                # To naprawia off-by-one error gdzie LLM czasami zwraca sum(group.count) < num_personas
                total_allocated = sum(group.count for group in allocation_plan.groups)
                if total_allocated < num_personas and allocation_plan.groups:
                    shortage = num_personas - total_allocated
                    logger.info(
                        f"🔧 Correcting allocation shortage: adding {shortage} personas to last group "
                        f"(LLM allocated {total_allocated}/{num_personas})"
                    )

                    # Zwiększ count ostatniej grupy
                    allocation_plan.groups[-1].count += shortage

                    # Dodaj brakujące persony do mapping (używając briefa ostatniej grupy)
                    last_group = allocation_plan.groups[-1]
                    if group_metadata:
                        last_metadata = group_metadata[-1]
                    else:
                        last_demographics = (
                            last_group.demographics
                            if isinstance(last_group.demographics, dict)
                            else dict(last_group.demographics)
                        )
                        last_metadata = _build_segment_metadata(
                            last_demographics,
                            last_group.brief,
                            last_group.allocation_reasoning,
                            len(allocation_plan.groups) - 1,
                        )
                    for i in range(persona_index, num_personas):
                        persona_group_mapping[i] = {
                            "brief": last_group.brief,
                            "graph_insights": [insight.model_dump() for insight in last_group.graph_insights],
                            "allocation_reasoning": last_group.allocation_reasoning,
                            "demographics": last_group.demographics
                            if isinstance(last_group.demographics, dict)
                            else dict(last_group.demographics),
                            "segment_characteristics": last_group.segment_characteristics,
                            **last_metadata,
                        }
                        persona_index += 1

                # WALIDACJA: Sprawdź czy wszystkie persony dostały briefe
                total_allocated = sum(group.count for group in allocation_plan.groups)
                if total_allocated != num_personas:
                    logger.warning(
                        f"⚠️ Allocation plan gap: expected {num_personas} personas, "
                        f"but allocation plan covers {total_allocated}. "
                        f"{num_personas - total_allocated} personas won't have orchestration briefs."
                    )
                elif persona_index < num_personas:
                    logger.warning(
                        f"⚠️ Brief mapping incomplete: mapped {persona_index}/{num_personas} personas. "
                        f"Last {num_personas - persona_index} personas won't have orchestration briefs."
                    )

                logger.info(f"📋 Mapped briefs to {len(persona_group_mapping)} personas")

            except Exception as orch_error:
                # Jeśli orchestration failuje, użyj FALLBACK allocation
                # Wygeneruje prosty plan bez Graph insights, ale persony nadal będą realistyczne
                logger.warning(
                    f"⚠️  Orchestration FAILED - using fallback allocation (degraded mode): {orch_error}",
                    exc_info=orch_error,
                    extra={"project_id": str(project_id)}
                )

                # Utwórz fallback plan alokacji
                fallback_plan_raw = _create_simple_fallback_allocation(
                    num_personas=num_personas,
                    target_demographics=target_demographics
                )

                # Convert fallback dict to Pydantic-compatible structure
                allocation_plan = type('obj', (object,), {
                    'total_personas': fallback_plan_raw['total_personas'],
                    'overall_context': fallback_plan_raw['overall_context'],
                    'groups': [
                        type('group', (object,), {
                            'count': g['count'],
                            'demographics': g['demographics'],
                            'brief': g['brief'],
                            'segment_characteristics': g['segment_characteristics'],
                            'allocation_reasoning': g['allocation_reasoning'],
                            'graph_insights': []  # Empty list for fallback
                        })
                        for g in fallback_plan_raw['groups']
                    ]
                })()

                # Mapuj fallback briefe do każdej persony
                persona_index = 0
                group_metadata: List[Dict[str, Optional[str]]] = []
                for group_index, group in enumerate(allocation_plan.groups):
                    demographics = group.demographics
                    segment_metadata = _build_segment_metadata(
                        demographics,
                        group.brief,
                        group.allocation_reasoning,
                        group_index,
                    )
                    group_metadata.append(segment_metadata)
                    for _ in range(group.count):
                        if persona_index < num_personas:
                            persona_group_mapping[persona_index] = {
                                "brief": group.brief,
                                "graph_insights": [],
                                "allocation_reasoning": group.allocation_reasoning,
                                "demographics": demographics,
                                "segment_characteristics": group.segment_characteristics,
                                **segment_metadata,
                            }
                            persona_index += 1

                logger.info(f"✅ Fallback mode: mapped briefs to {len(persona_group_mapping)} personas")

            # Kontrolowana współbieżność pozwala przyspieszyć generowanie bez przeciążania modelu
            concurrency_limit = _calculate_concurrency_limit(num_personas, adversarial_mode)
            semaphore = asyncio.Semaphore(concurrency_limit)

            logger.info(
                f"Starting LLM generation for {num_personas} personas with concurrency={concurrency_limit}. "
                f"ALL data (demographics, psychographics, names, occupations) generated by LLM from orchestration briefs.",
                extra={"project_id": str(project_id), "concurrency_limit": concurrency_limit},
            )

            personas_data: List[Dict[str, Any]] = []
            batch_payloads: List[Dict[str, Any]] = []
            saved_count = 0
            # Mniejsze batch-e oznaczają szybszą widoczność danych w UI i niższe zużycie pamięci
            batch_size = max(1, min(10, num_personas // 4 or 1))

            async def persist_batch() -> None:
                """Zapisz aktualny batch person do bazy – komentarz po polsku, zgodnie z prośbą."""
                nonlocal saved_count
                if not batch_payloads:
                    return
                try:
                    db.add_all([Persona(**data) for data in batch_payloads])
                    await db.commit()
                    saved_count += len(batch_payloads)
                    logger.info(
                        "Persisted persona batch",
                        extra={
                            "project_id": str(project_id),
                            "batch_size": len(batch_payloads),
                            "saved_total": saved_count,
                            "target": num_personas,
                        },
                    )
                except Exception as commit_error:  # pragma: no cover - zabezpieczenie awaryjne
                    await db.rollback()
                    logger.error(
                        "Nie udało się zapisać partii wygenerowanych person.",
                        exc_info=commit_error,
                        extra={"project_id": str(project_id), "batch_size": len(batch_payloads)},
                    )
                    raise
                finally:
                    batch_payloads.clear()

            async def create_single_persona(idx: int):
                """Generuj pojedynczą personę z orchestration brief (demographics + psychographics)"""
                async with semaphore:
                    # WYMAGANE: Orchestration brief musi istnieć dla każdej persony
                    if idx not in persona_group_mapping:
                        logger.error(
                            f"❌ Missing orchestration brief for persona {idx} - cannot generate!",
                            extra={"project_id": str(project_id), "index": idx}
                        )
                        raise RuntimeError(
                            f"Orchestration brief required for persona {idx}. "
                            "Cannot generate persona without demographic allocation plan."
                        )

                    # Demographics z orchestration (AUTORYTATYWNE)
                    demo_profile = persona_group_mapping[idx]["demographics"]

                    # Psychographics - sampling (Big Five + Hofstede)
                    psych_profile = {
                        **generator.sample_big_five_traits(),
                        **generator.sample_cultural_dimensions()
                    }

                    # === COMPREHENSIVE PERSONA GENERATION ===
                    # LLM generuje WSZYSTKIE dane razem (demographics + background + values + interests)
                    # demographic_guidance jest tylko sugestią, nie wymogiem

                    # Pobierz RAG context jeśli use_rag=True
                    rag_context_str = None
                    if use_rag and hasattr(generator, 'rag_service') and generator.rag_service:
                        try:
                            rag_data = await generator._get_rag_context_for_persona(demo_profile)
                            if rag_data:
                                rag_context_str = rag_data.get('context')
                        except Exception as rag_error:
                            logger.warning(f"RAG context failed for persona {idx}: {rag_error}")

                    # Call comprehensive generation (LLM generuje ALL DATA)
                    persona_data = await generator.generate_comprehensive_persona(
                        orchestration_brief=persona_group_mapping[idx]["brief"],
                        segment_characteristics=persona_group_mapping[idx]["segment_characteristics"],
                        demographic_guidance=demo_profile,  # Tylko sugestia, nie requirement!
                        rag_context=rag_context_str,
                        psychological_profile=psych_profile
                    )

                    if (idx + 1) % max(1, batch_size) == 0 or idx == num_personas - 1:
                        logger.info(
                            "Generated personas chunk (comprehensive)",
                            extra={"project_id": str(project_id), "generated": idx + 1, "target": num_personas},
                        )

                    # Return idx, persona_data (NIE result tuple!)
                    return idx, persona_data, demo_profile, psych_profile

            # Generate tasks for all personas (demographics z orchestration, psychographics sampled)
            tasks = [asyncio.create_task(create_single_persona(i)) for i in range(num_personas)]

            try:
                for future in asyncio.as_completed(tasks):
                    try:
                        idx, persona_data, demographic, psychological = await future
                    except Exception as gen_error:  # pragma: no cover - logowanie błędów zadań
                        logger.error(
                            "Persona generation coroutine failed.",
                            exc_info=gen_error,
                            extra={"project_id": str(project_id)},
                        )
                        continue

                    # ===  COMPREHENSIVE GENERATION - persona_data jest dict z ALL DATA ===
                    # LLM już wygenerował wszystko: demographics, background_story, values, interests
                    # Brak JSON parsing, brak polonizacji post-processing!

                    # Extract data z persona_data (wszystko PL, wygenerowane przez LLM)
                    age = persona_data.get("age")
                    gender_value = persona_data.get("gender")
                    location_value = persona_data.get("location")
                    education_value = persona_data.get("education_level")
                    income_value = persona_data.get("income_bracket")
                    occupation = persona_data.get("occupation")
                    full_name = persona_data.get("full_name")
                    background_story = persona_data.get("background_story", "")
                    values = persona_data.get("values", [])
                    interests = persona_data.get("interests", [])

                    # Fallback dla krytycznych pól (jeśli LLM zawiódł)
                    if not full_name or full_name == "N/A":
                        full_name = _fallback_full_name(gender_value, age)
                        logger.warning(
                            f"❌ LLM failed to generate full_name for persona {idx}, using fallback: {full_name}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    if not occupation or occupation == "N/A":
                        occupation = "Specjalista"  # Generic fallback
                        logger.error(
                            f"❌ LLM failed to generate occupation for persona {idx}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    if not background_story:
                        logger.warning(
                            f"Missing background_story for persona {idx}",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    # persona_title jako alias dla occupation (backward compatibility)
                    persona_title = persona_data.get("persona_title") or occupation

                    # Headline fallback
                    headline = persona_data.get("headline")
                    if not headline or headline == "N/A":
                        headline = _compose_headline(
                            full_name, persona_title, occupation, location_value
                        )
                        logger.warning(
                            f"Missing headline for persona {idx}, using generated: {headline}",
                            extra={"project_id": str(project_id), "index": idx}
                        )

                    # Values i interests check (nie logi error tylko jeśli brak)
                    if not values:
                        logger.warning(
                            f"⚠️  LLM failed to generate values for persona {idx}",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    if not interests:
                        logger.warning(
                            f"⚠️  LLM failed to generate interests for persona {idx}",
                            extra={"project_id": str(project_id), "index": idx},
                        )

                    # RAG citations i details - initialize with orchestration data
                    rag_citations = None  # Comprehensive generation doesn't return citations yet
                    rag_context_details = {}
                    rag_context_used = False  # Set to True once we integrate RAG with comprehensive

                    # Dodaj orchestration reasoning do rag_context_details (jeśli istnieje)
                    if idx in persona_group_mapping:
                        mapping_entry = persona_group_mapping[idx]
                        segment_name_meta = mapping_entry.get("segment_name")
                        segment_id_meta = mapping_entry.get("segment_id")
                        segment_description_meta = mapping_entry.get("segment_description")
                        segment_context_meta = mapping_entry.get("segment_social_context")

                        rag_context_details["orchestration_reasoning"] = {
                            "brief": mapping_entry["brief"],
                            "graph_insights": mapping_entry["graph_insights"],
                            "allocation_reasoning": mapping_entry["allocation_reasoning"],
                            "demographics": mapping_entry["demographics"],
                            "segment_characteristics": mapping_entry["segment_characteristics"],
                            "overall_context": allocation_plan.overall_context if allocation_plan else None,
                            "segment_name": segment_name_meta,
                            "segment_id": segment_id_meta,
                            "segment_description": segment_description_meta,
                            "segment_social_context": segment_context_meta,
                        }

                        if segment_name_meta and "segment_name" not in rag_context_details:
                            rag_context_details["segment_name"] = segment_name_meta
                        if segment_id_meta and "segment_id" not in rag_context_details:
                            rag_context_details["segment_id"] = segment_id_meta
                        if segment_description_meta and "segment_description" not in rag_context_details:
                            rag_context_details["segment_description"] = segment_description_meta
                        if segment_context_meta and "segment_social_context" not in rag_context_details:
                            rag_context_details["segment_social_context"] = segment_context_meta
                        if mapping_entry["segment_characteristics"] and "segment_characteristics" not in rag_context_details:
                            rag_context_details["segment_characteristics"] = mapping_entry["segment_characteristics"]

                    persona_payload = {
                        "project_id": project_id,
                        "full_name": full_name,
                        "persona_title": persona_title,
                        "headline": headline,
                        "age": age,
                        "gender": gender_value,
                        "location": location_value,
                        "education_level": education_value,
                        "income_bracket": income_value,
                        "occupation": occupation,
                        "background_story": background_story,
                        "values": values,
                        "interests": interests,
                        "personality_prompt": None,  # Comprehensive generation doesn't use personality_prompt
                        "rag_context_used": rag_context_used,
                        "rag_citations": rag_citations,
                        "rag_context_details": rag_context_details,  # NOWE POLE
                        **psychological
                    }

                    if idx in persona_group_mapping:
                        mapping_entry = persona_group_mapping[idx]
                        if mapping_entry.get("segment_id"):
                            persona_payload["segment_id"] = mapping_entry["segment_id"]
                        if mapping_entry.get("segment_name"):
                            persona_payload["segment_name"] = mapping_entry["segment_name"]

                    # === VALIDATION: SPRAWDŹ SPÓJNOŚĆ DEMOGRAPHICS ===
                    # Validate że generated persona pasuje do orchestration demographics
                    if idx in persona_group_mapping:
                        orch_demo = persona_group_mapping[idx]["demographics"]
                        mismatches = []

                        # Check gender
                        expected_gender = _polishify_gender(orch_demo.get("gender", ""))
                        if expected_gender and persona_payload["gender"] != expected_gender:
                            mismatches.append(
                                f"gender: got '{persona_payload['gender']}', expected '{expected_gender}'"
                            )

                        # Check age range
                        expected_age_range = orch_demo.get("age", "")
                        if expected_age_range and "-" in expected_age_range:
                            try:
                                min_age, max_age = map(int, expected_age_range.split("-"))
                                if not (min_age <= persona_payload["age"] <= max_age):
                                    mismatches.append(
                                        f"age: {persona_payload['age']} not in range {expected_age_range}"
                                    )
                            except ValueError:
                                pass

                        # Check education (basic comparison - might have different formats)
                        expected_education = orch_demo.get("education", "")
                        if expected_education:
                            # Normalize for comparison
                            norm_expected_ed = _polishify_education(expected_education)
                            if persona_payload["education_level"] != norm_expected_ed:
                                mismatches.append(
                                    f"education: got '{persona_payload['education_level']}', "
                                    f"expected '{norm_expected_ed}'"
                                )

                        # Log mismatches jeśli znaleziono
                        if mismatches:
                            logger.warning(
                                f"⚠️  Demographics mismatch for persona {idx} ('{full_name}'): "
                                f"{'; '.join(mismatches)}",
                                extra={
                                    "project_id": str(project_id),
                                    "persona_index": idx,
                                    "full_name": full_name,
                                    "mismatches": mismatches,
                                }
                            )

                    personas_data.append(persona_payload)
                    batch_payloads.append(persona_payload)

                    if len(batch_payloads) >= batch_size:
                        await persist_batch()
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

            # Finalne opróżnienie bufora
            await persist_batch()

            if not personas_data:
                logger.warning("No personas were generated successfully.", extra={"project_id": str(project_id)})
                return

            # Walidacja jakości wygenerowanych person
            validator = PersonaValidator()
            validation_results = validator.validate_personas(personas_data)
            if not validation_results["is_valid"]:
                logger.warning("Persona validation found issues.", extra=validation_results)

            # NOTE: Statistical distribution validation (chi-square) USUNIĘTA
            # Demographics są teraz generowane przez LLM z orchestration briefs,
            # nie samplingowane z rozkładu statystycznego.
            # Orchestration service (Gemini 2.5 Pro) zapewnia odpowiednią alokację demograficzną.

            logger.info("Persona generation task completed.", extra={"project_id": str(project_id), "count": len(personas_data)})
    except Exception as e:
        logger.error(f"CRITICAL ERROR in persona generation task", exc_info=e)


def _normalize_rag_citations(citations: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """
    Normalizuje RAG citations do aktualnego schematu RAGCitation.

    Stary format (przed refactorem):
    {
        "text": str,
        "score": float,
        "metadata": {"title": str, ...}
    }

    Nowy format (RAGCitation schema):
    {
        "document_title": str,
        "chunk_text": str,
        "relevance_score": float
    }

    Args:
        citations: Lista citations (może być None lub pusta)

    Returns:
        Lista citations w nowym formacie lub None jeśli input był None
    """
    if not citations:
        return citations

    normalized = []
    for citation in citations:
        if not isinstance(citation, dict):
            logger.warning(f"Invalid citation type: {type(citation)}, skipping")
            continue

        # Sprawdź czy to stary format (ma 'text' zamiast 'chunk_text')
        if 'text' in citation and 'chunk_text' not in citation:
            # Stary format - przekształć
            normalized_citation = {
                "document_title": citation.get("metadata", {}).get("title", "Unknown Document"),
                "chunk_text": citation.get("text", ""),
                "relevance_score": abs(float(citation.get("score", 0.0)))  # abs() bo stare scores były ujemne
            }
            normalized.append(normalized_citation)
        elif 'chunk_text' in citation:
            # Nowy format - użyj bez zmian
            normalized.append(citation)
        else:
            # Nieprawidłowy format - spróbuj wyekstraktować co się da
            logger.warning(f"Unknown citation format: {list(citation.keys())}")
            normalized_citation = {
                "document_title": citation.get("document_title") or citation.get("metadata", {}).get("title", "Unknown Document"),
                "chunk_text": citation.get("chunk_text") or citation.get("text", ""),
                "relevance_score": abs(float(citation.get("relevance_score") or citation.get("score", 0.0)))
            }
            normalized.append(normalized_citation)

    return normalized if normalized else None



@router.get("/projects/{project_id}/personas", response_model=List[PersonaResponse])
async def list_personas(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List personas for a project"""
    await get_project_for_user(project_id, current_user, db)
    result = await db.execute(
        select(Persona)
        .where(
            Persona.project_id == project_id,
            Persona.is_active.is_(True),
            Persona.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(limit)
    )
    personas = result.scalars().all()

    # Normalizuj rag_citations dla każdej persony (backward compatibility)
    for persona in personas:
        if persona.rag_citations:
            persona.rag_citations = _normalize_rag_citations(persona.rag_citations)

    return personas


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific persona"""
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Normalizuj rag_citations (backward compatibility)
    if persona.rag_citations:
        persona.rag_citations = _normalize_rag_citations(persona.rag_citations)

    return persona


@router.delete("/personas/{persona_id}", response_model=PersonaDeleteResponse)
async def delete_persona(
    persona_id: UUID,
    delete_request: PersonaDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete persona z audit logging

    Args:
        persona_id: UUID persony do usunięcia
        delete_request: Powód usunięcia (reason + optional reason_detail)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDeleteResponse

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą usuwać własne persony
        - Production: Tylko Admin może usuwać (TODO: add RBAC check)

    Audit:
        - Loguje delete action z reason w persona_audit_log
    """
    persona = await get_persona_for_user(persona_id, current_user, db)

    if persona.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Persona already deleted",
        )

    deleted_at = datetime.utcnow()
    undo_deadline = deleted_at + timedelta(seconds=30)
    permanent_delete_at = deleted_at + timedelta(days=90)

    # Miękkie usunięcie rekordu
    persona.is_active = False
    persona.deleted_at = deleted_at
    persona.deleted_by = current_user.id

    # Log delete action (audit trail)
    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="delete",
        details={
            "reason": delete_request.reason,
            "reason_detail": delete_request.reason_detail,
        },
        db=db,
    )

    await db.commit()

    return PersonaDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="deleted",
        deleted_at=deleted_at,
        deleted_by=current_user.id,
        undo_available_until=undo_deadline,
        permanent_deletion_scheduled_at=permanent_delete_at,
        message="Persona deleted successfully. You can undo this action within 30 seconds.",
    )


@router.post("/personas/{persona_id}/undo-delete", response_model=PersonaUndoDeleteResponse)
async def undo_delete_persona(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Przywróć personę jeśli okno undo (30s) nie wygasło."""
    persona = await get_persona_for_user(
        persona_id,
        current_user,
        db,
        include_inactive=True,
    )

    if persona.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona is not deleted")

    undo_deadline = persona.deleted_at + timedelta(seconds=30)
    now = datetime.utcnow()
    if now > undo_deadline:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Undo window expired. Persona can be restored from Archived view.",
            headers={
                "X-Undo-Deadline": undo_deadline.isoformat(),
                "X-Deleted-At": persona.deleted_at.isoformat(),
            },
        )

    persona.is_active = True
    persona.deleted_at = None
    persona.deleted_by = None

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="undo_delete",
        details={"source": "undo"},
        db=db,
    )

    await db.commit()

    return PersonaUndoDeleteResponse(
        persona_id=persona_id,
        full_name=persona.full_name,
        status="active",
        restored_at=now,
        restored_by=current_user.id,
        message="Persona restored successfully",
    )


@router.post(
    "/personas/{persona_id}/actions/messaging",
    response_model=PersonaMessagingResponse,
)
@limiter.limit("10/hour")
async def generate_persona_messaging(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    payload: PersonaMessagingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    persona = await get_persona_for_user(persona_id, current_user, db)
    messaging_service = PersonaMessagingService()
    result = await messaging_service.generate_messaging(
        persona,
        tone=payload.tone,
        message_type=payload.message_type,
        num_variants=payload.num_variants,
        context=payload.context,
    )

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="messaging",
        details={
            "tone": payload.tone,
            "type": payload.message_type,
            "variants": payload.num_variants,
        },
        db=db,
    )

    return PersonaMessagingResponse(**result)


@router.post(
    "/personas/{persona_id}/actions/compare",
    response_model=PersonaComparisonResponse,
)
@limiter.limit("30/minute")
async def compare_personas_endpoint(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    payload: PersonaComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    primary_persona = await get_persona_for_user(persona_id, current_user, db)
    comparison_service = PersonaComparisonService(db)
    data = await comparison_service.compare_personas(
        primary_persona,
        [str(pid) for pid in payload.persona_ids],
        sections=payload.sections,
    )

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="compare",
        details={
            "persona_ids": [str(pid) for pid in payload.persona_ids],
            "sections": payload.sections,
        },
        db=db,
    )

    return PersonaComparisonResponse(**data)


@router.post(
    "/personas/{persona_id}/actions/export",
    response_model=PersonaExportResponse,
)
@limiter.limit("30/minute")
async def export_persona_details(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    payload: PersonaExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.format != "json":
        raise HTTPException(status_code=400, detail="Only JSON export is supported in this environment.")

    details_service = PersonaDetailsService(db)
    details = await details_service.get_persona_details(
        persona_id=persona_id,
        user_id=current_user.id,
        force_refresh=False,
    )

    # Note: Removed "journey" section (deprecated customer_journey field)
    # Available sections: ["overview", "profile", "needs", "insights"]
    sections = payload.sections or ["overview", "profile", "needs", "insights"]
    content: Dict[str, Any] = {}

    if "overview" in sections:
        content["overview"] = {
            # kpi_snapshot removed - deprecated field
            "rag_citations": details.rag_citations,
        }
    if "profile" in sections:
        content["profile"] = {
            "full_name": details.full_name,
            "persona_title": details.persona_title,
            "headline": details.headline,
            "demographics": {
                "age": details.age,
                "gender": details.gender,
                "location": details.location,
                "education_level": details.education_level,
                "income_bracket": details.income_bracket,
                "occupation": details.occupation,
            },
            "big_five": details.big_five,
            "values": details.values,
            "interests": details.interests,
            "background_story": details.background_story,
        }
    # "journey" section removed - customer_journey field deprecated
    # For journey data, use PersonaJourneyService directly
    if "needs" in sections:
        content["needs"] = details.needs_and_pains.model_dump(mode="json") if details.needs_and_pains else None
    if "insights" in sections:
        content["insights"] = {
            "rag_context_details": details.rag_context_details,
            "audit_log": [entry.model_dump(mode="json") for entry in details.audit_log],
        }

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="export",
        details={"format": payload.format, "sections": sections},
        db=db,
    )

    return PersonaExportResponse(format="json", sections=sections, content=content)


@router.get("/personas/{persona_id}/reasoning", response_model=PersonaReasoningResponse)
async def get_persona_reasoning(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz szczegółowe reasoning persony (dla zakładki 'Uzasadnienie' w UI)

    Zwraca:
    - orchestration_brief: Zwięzły (900-1200 znaków) edukacyjny brief od Gemini 2.5 Pro
    - graph_insights: Lista wskaźników z Graph RAG z wyjaśnieniami "dlaczego to ważne"
    - allocation_reasoning: Dlaczego tyle person w tej grupie demograficznej
    - demographics: Docelowa demografia tej grupy
    - overall_context: Ogólny kontekst społeczny Polski

    Output style: Edukacyjny, konwersacyjny, wyjaśniający, production-ready

    Raises:
        HTTPException 404: Jeśli persona nie istnieje lub nie ma reasoning data
    """
    # Pobierz personę (weryfikacja uprawnień)
    persona = await get_persona_for_user(persona_id, current_user, db)

    # Graceful handling: zwróć pustą response jeśli brak orchestration data
    # (zamiast 404 - lepsze UX)
    rag_details: Dict[str, Any] = persona.rag_context_details or {}
    if not rag_details:
        logger.warning(
            "Persona %s nie ma rag_context_details - zwracam pustą response", persona_id
        )
        return PersonaReasoningResponse(
            orchestration_brief=None,
            graph_insights=[],
            allocation_reasoning=None,
            demographics=None,
            overall_context=None,
        )

    orch_reasoning: Dict[str, Any] = rag_details.get("orchestration_reasoning") or {}
    if not orch_reasoning:
        logger.warning(
            "Persona %s nie ma orchestration_reasoning - korzystam tylko z danych RAG",
            persona_id,
        )

    # Parsuj graph insights z orchestration lub fallbacku
    graph_insights: List[GraphInsightResponse] = []
    raw_graph_insights = orch_reasoning.get("graph_insights") or rag_details.get(
        "graph_insights", []
    )
    for insight_dict in raw_graph_insights or []:
        try:
            graph_insights.append(GraphInsightResponse(**insight_dict))
        except Exception as exc:
            logger.warning(
                "Failed to parse graph insight: %s, insight=%s", exc, insight_dict
            )

    # Fallback: konwertuj surowe węzły grafu na insights
    if not graph_insights and rag_details.get("graph_nodes"):
        for node in rag_details["graph_nodes"]:
            converted = _graph_node_to_insight_response(node)
            if converted:
                graph_insights.append(converted)

    # Wyprowadź pola segmentowe i kontekstowe
    segment_name = orch_reasoning.get("segment_name") or rag_details.get("segment_name")
    segment_description = orch_reasoning.get("segment_description") or rag_details.get(
        "segment_description"
    )
    segment_social_context = (
        orch_reasoning.get("segment_social_context")
        or rag_details.get("segment_social_context")
        or rag_details.get("segment_context")
    )
    segment_characteristics = (
        orch_reasoning.get("segment_characteristics")
        or rag_details.get("segment_characteristics")
        or []
    )

    orchestration_brief = orch_reasoning.get("brief") or rag_details.get("brief")
    allocation_reasoning = orch_reasoning.get("allocation_reasoning") or rag_details.get(
        "allocation_reasoning"
    )
    demographics = orch_reasoning.get("demographics") or rag_details.get("demographics")
    overall_context = (
        orch_reasoning.get("overall_context")
        or rag_details.get("overall_context")
        or rag_details.get("graph_context")
    )

    if not segment_name or not segment_social_context or not segment_description:
        fallback_demographics = (
            orch_reasoning.get("demographics")
            or rag_details.get("demographics")
            or {
                "age": str(persona.age) if persona.age else None,
                "gender": persona.gender,
                "education": persona.education_level,
                "income": persona.income_bracket,
                "location": persona.location,
            }
        )
        if not isinstance(fallback_demographics, dict):
            try:
                fallback_demographics = dict(fallback_demographics)
            except Exception:
                fallback_demographics = {
                    "age": str(persona.age) if persona.age else None,
                    "gender": persona.gender,
                    "education": persona.education_level,
                    "income": persona.income_bracket,
                    "location": persona.location,
                }

        fallback_meta = _build_segment_metadata(
            fallback_demographics,
            orch_reasoning.get("brief") or rag_details.get("brief"),
            allocation_reasoning,
            0,
        )
        segment_name = segment_name or fallback_meta.get("segment_name")
        segment_description = segment_description or fallback_meta.get("segment_description")
        segment_social_context = segment_social_context or fallback_meta.get("segment_social_context")
        if not segment_characteristics:
            segment_characteristics = rag_details.get("segment_characteristics") or []

    response = PersonaReasoningResponse(
        orchestration_brief=orchestration_brief,
        graph_insights=graph_insights,
        allocation_reasoning=allocation_reasoning,
        demographics=demographics,
        overall_context=overall_context,
        segment_name=segment_name,
        segment_id=orch_reasoning.get("segment_id") or rag_details.get("segment_id"),
        segment_description=segment_description,
        segment_social_context=segment_social_context,
        segment_characteristics=segment_characteristics,
    )

    return response


@router.post("/personas/{persona_id}/narratives/regenerate")
@limiter.limit("10/hour")  # Rate limit: 10 regenerations/h per user
async def regenerate_persona_narratives(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regeneruje narracje dla persony (force regeneration, bypass cache).

    Rate limiting:
    - 10 regeneracji/h per user (global limit)
    - Używa Redis counter dla tracking

    Args:
        persona_id: UUID persony
        db: DB session
        current_user: Authenticated user

    Returns:
        {
            "narratives": PersonaNarratives,
            "status": "ok" | "degraded" | "offline",
            "regenerated_at": timestamp
        }

    Raises:
        HTTPException 404: Persona nie istnieje
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Generation failed

    Audit:
        - Loguje "narratives_regenerate" action w audit log
    """
    # Verify access
    await get_persona_for_user(persona_id, current_user, db)

    # Regenerate narratives (force_regenerate=True)
    narrative_service = PersonaNarrativeService()
    try:
        narratives, status = await narrative_service.get_narratives(
            persona_id=persona_id,
            scope='all',
            force_regenerate=True  # Force bypass cache
        )

        # Log action
        audit_service = PersonaAuditService()
        await audit_service.log_action(
            persona_id=persona_id,
            user_id=current_user.id,
            action="narratives_regenerate",
            details={
                "status": status,
                "has_narratives": narratives is not None
            },
            db=db,
        )

        # Return result
        return {
            "narratives": narratives,
            "status": status,
            "regenerated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(
            f"Failed to regenerate narratives for persona {persona_id}: {e}",
            exc_info=e,
            extra={"persona_id": str(persona_id), "user_id": str(current_user.id)}
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to regenerate narratives. Please try again later."
        )


@router.get("/personas/{persona_id}/details", response_model=PersonaDetailsResponse)
async def get_persona_details(
    persona_id: UUID,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz pełny detail view persony (MVP)

    Pełny widok szczegółowy persony z:
    - Base persona data (demographics, psychographics)
    - Needs and pains (JTBD, desired outcomes, pain points - opcjonalne)
    - RAG insights (z rag_context_details)
    - Audit log (last 20 actions)

    Note: KPI snapshot i customer journey zostały usunięte z modelu.
    Dla KPI metrics użyj PersonaKPIService, dla journey - PersonaJourneyService.

    Args:
        persona_id: UUID persony
        force_refresh: Wymuś recalculation (bypass cache)
        db: DB session
        current_user: Authenticated user

    Returns:
        PersonaDetailsResponse z pełnym detail view

    RBAC:
        - MVP: Wszyscy zalogowani użytkownicy mogą przeglądać persony
        - Production: Role-based permissions (Viewer+)

    Performance:
        - Cache hit: < 50ms (Redis) - TODO: implement caching
        - Cache miss: < 500ms (parallel fetch + 1 DB query)

    Audit:
        - Loguje "view" action w persona_audit_log (async, non-blocking)
    """
    # Verify access
    await get_persona_for_user(persona_id, current_user, db)

    # Fetch details (orchestration service)
    details_service = PersonaDetailsService(db)
    try:
        details = await details_service.get_persona_details(
            persona_id=persona_id,
            user_id=current_user.id,
            force_refresh=force_refresh,
        )
        return details
    except ValueError as e:
        # Persona not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error(f"Failed to fetch persona details: {e}", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch persona details. Please try again later.",
        )
