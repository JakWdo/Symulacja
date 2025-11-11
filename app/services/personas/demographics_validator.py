"""
Walidacja i ekstrakcja danych demograficznych z tekstów.

Ten moduł zawiera narzędzia do:
- Walidacji czy tekst wygląda na polski
- Ekstrakcji wieku z background stories
- Ekstrakcji imion i nazwisk z background stories
- Ekstrakcji polskich lokalizacji z tekstów

Użycie:
    age = extract_age_from_story(story)
    name = infer_full_name(story)
    is_polish = looks_polish_phrase("specjalista ds. marketingu")
"""

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# STAŁE - Wzorce i Słowniki
# ============================================================================

_POLISH_CHARACTERS = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"

_POLISH_CITY_LOOKUP = {
    "warszawa": "Warszawa",
    "krakow": "Kraków",
    "wroclaw": "Wrocław",
    "poznan": "Poznań",
    "gdansk": "Gdańsk",
    "szczecin": "Szczecin",
    "bydgoszcz": "Bydgoszcz",
    "lublin": "Lublin",
    "katowice": "Katowice",
    "bialystok": "Białystok",
    "gdynia": "Gdynia",
    "czestochowa": "Częstochowa",
    "radom": "Radom",
    "sosnowiec": "Sosnowiec",
    "torun": "Toruń",
    "kielce": "Kielce",
    "gliwice": "Gliwice",
    "zabrze": "Zabrze",
    "bytom": "Bytom",
    "olsztyn": "Olsztyn",
    "rzeszow": "Rzeszów",
    "ruda slaska": "Ruda Śląska",
    "rybnik": "Rybnik",
    "tychy": "Tychy",
    "dabrowa gornicza": "Dąbrowa Górnicza",
    "lodz": "Łódź",
    "opole": "Opole",
    "trojmiasto": "Trójmiasto",
}

# Regex patterns dla ekstrakcji z background stories
_NAME_FROM_STORY_PATTERN = re.compile(r"^(?P<name>[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)+)")
_AGE_IN_STORY_PATTERN = re.compile(r"(?P<age>\d{1,2})-year-old", re.IGNORECASE)
_POLISH_AGE_PATTERNS = [
    re.compile(r"(?:ma|mam|wieku)\s+(?P<age>\d{1,2})\s+lat", re.IGNORECASE),
    re.compile(r"(?P<age>\d{1,2})-letni[a]?", re.IGNORECASE),
    re.compile(r"lat\s+(?P<age>\d{1,2})", re.IGNORECASE),
]


# ============================================================================
# Funkcje Pomocnicze Normalizacji
# ============================================================================

def normalize_text(value: str | None) -> str:
    """
    Usuń diakrytyki i sprowadź tekst do małych liter – pomocne przy dopasowaniach.

    Args:
        value: Tekst do normalizacji

    Returns:
        Znormalizowany tekst (lowercase, bez diakrytyków)

    Example:
        >>> normalize_text("Kraków")
        'krakow'
    """
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return stripped.lower().strip()


# ============================================================================
# Funkcje Walidacji
# ============================================================================

def looks_polish_phrase(text: str | None) -> bool:
    """
    Sprawdź heurystycznie czy tekst wygląda na polski (znaki diakrytyczne, słowa kluczowe).

    Args:
        text: Tekst do sprawdzenia

    Returns:
        True jeśli tekst wygląda na polski
    """
    if not text:
        return False
    lowered = text.strip().lower()
    if any(char in text for char in _POLISH_CHARACTERS):
        return True
    keywords = ["specjalista", "menedżer", "koordynator", "student", "uczeń", "właściciel", "kierownik", "logistyk"]
    return any(keyword in lowered for keyword in keywords)


# ============================================================================
# Funkcje Ekstrakcji
# ============================================================================

def extract_polish_location_from_story(story: str | None) -> str | None:
    """
    Spróbuj znaleźć polską lokalizację wewnątrz historii tła persony.

    Obsługuje fleksję (Warszawie, Gdańsku, z Krakowa).

    Args:
        story: Background story persony

    Returns:
        Nazwa polskiego miasta lub None

    Example:
        >>> story = "Mieszka w Gdańsku od 5 lat."
        >>> extract_polish_location_from_story(story)
        'Gdańsk'
    """
    if not story:
        return None
    normalized_story = normalize_text(story)
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


def infer_full_name(background_story: str | None) -> str | None:
    """
    Ekstraktuj pełne imię i nazwisko z background_story (regex pattern).

    Args:
        background_story: Historia życiowa persony

    Returns:
        Pełne imię lub None

    Example:
        >>> story = "Jan Kowalski mieszka w Warszawie..."
        >>> infer_full_name(story)
        'Jan Kowalski'
    """
    if not background_story:
        return None
    match = _NAME_FROM_STORY_PATTERN.match(background_story.strip())
    if match:
        return match.group('name')
    return None


def extract_age_from_story(background_story: str | None) -> int | None:
    """
    Ekstraktuj wiek z background_story (wspiera polski i angielski tekst).

    Patterns:
    - Angielski: "32-year-old"
    - Polski: "ma 32 lata", "32-letni", "lat 32"

    Args:
        background_story: Historia życiowa persony

    Returns:
        Wyekstraktowany wiek (10-100) lub None jeśli nie znaleziono
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
