"""
Utility Functions - Persona API

Wspólne funkcje pomocnicze dla endpointów person:
- Konwersje danych (EN→PL, normalizacja)
- Formatowanie opisów segmentów
- Ekstrakcja danych z tekstów
- Walidacja i sanitacja

Te funkcje są używane przez wszystkie moduły endpoints.
"""

import logging
import random
import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from app.services.personas import PersonaGeneratorLangChain
from app.core.constants import (
    DEFAULT_OCCUPATIONS,
    POLISH_LOCATIONS,
    POLISH_INCOME_BRACKETS,
    POLISH_EDUCATION_LEVELS,
    POLISH_VALUES,
    POLISH_INTERESTS,
    POLISH_OCCUPATIONS,
)

logger = logging.getLogger(__name__)

# Alias for backward compatibility
PreferredPersonaGenerator = PersonaGeneratorLangChain


def _graph_node_to_insight_response(node: Dict[str, Any]) -> Optional[Any]:
    """Konwertuje surowy węzeł grafu (Neo4j) na GraphInsightResponse."""
    from app.schemas.persona import GraphInsightResponse

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
    """Ustal możliwie polski tytuł zawodowy bazując na dostępnych danych."""
    candidate = personality.get("persona_title") or personality.get("occupation")
    if candidate and _looks_polish_phrase(candidate):
        return _format_job_title(candidate)

    if background_story:
        for pattern in _BACKGROUND_JOB_PATTERNS:
            match = pattern.search(background_story)
            if match:
                job = match.group("job").strip()
                if job:
                    return _format_job_title(job)

    # Jeżeli AI nie zwróciło spójnego polskiego zawodu – losuj realistyczny zawód z rozkładu
    occupation = _select_weighted(POLISH_OCCUPATIONS)
    if occupation:
        return occupation

    # Fallback na wylosowaną angielską listę (ostatnia linia obrony)
    return random.choice(DEFAULT_OCCUPATIONS) if DEFAULT_OCCUPATIONS else "Specjalista"


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
        labels = [f"{country} - Urban hub" for country in countries]
        return _normalize_weights({label: 1 / len(labels) for label in labels})

    urbanicity = advanced_options.get('urbanicity')
    if urbanicity == 'urban':
        return base_locations
    if urbanicity == 'suburban':
        return _normalize_weights({
            'Suburban Midwest, USA': 0.25,
            'Suburban Northeast, USA': 0.25,
            'Sunbelt Suburb, USA': 0.2,
            'Other': 0.3,
        })
    if urbanicity == 'rural':
        return _normalize_weights({
            'Rural Midwest, USA': 0.35,
            'Rural South, USA': 0.25,
            'Mountain Town, USA': 0.2,
            'Other Rural Area': 0.2,
        })

    return base_locations


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


__all__ = [
    # Generator
    "_get_persona_generator",
    "_calculate_concurrency_limit",

    # Text processing
    "_normalize_text",
    "_sanitize_brief_text",
    "_normalize_rag_citations",

    # Polish localization
    "_polishify_gender",
    "_polishify_education",
    "_polishify_income",
    "_ensure_polish_location",
    "_looks_polish_phrase",

    # Name and age extraction
    "_infer_full_name",
    "_fallback_full_name",
    "_extract_age_from_story",

    # Occupation inference
    "_infer_polish_occupation",
    "_get_consistent_occupation",
    "_format_job_title",

    # Segment building
    "_compose_segment_name",
    "_compose_segment_description",
    "_build_segment_metadata",
    "_slugify_segment",

    # Distribution utilities
    "_select_weighted",
    "_normalize_weights",
    "_normalize_distribution",
    "_coerce_distribution",

    # Age group utilities
    "_age_group_bounds",
    "_age_group_overlaps",
    "_apply_age_preferences",
    "_apply_gender_preferences",
    "_build_location_distribution",

    # Formatting
    "_compose_headline",
    "_ensure_story_alignment",
    "_fallback_polish_list",

    # Graph utilities
    "_graph_node_to_insight_response",
]
