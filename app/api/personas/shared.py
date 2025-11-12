"""Shared utilities for persona API endpoints.

This module contains shared helper functions and state used across
generation_endpoints, validation_endpoints, and orchestration_endpoints.
"""

import logging
import random
import re
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

# Shared state for running background tasks
_running_tasks: set[UUID] = set()


# ===== NAME EXTRACTION AND GENERATION =====


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


# ===== AGE AND DEMOGRAPHIC EXTRACTION =====


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


# ===== OCCUPATION EXTRACTION =====


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


# ===== LIST FALLBACKS =====


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
