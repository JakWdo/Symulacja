"""
Distribution Validators - Helper functions do walidacji i parsowania rozkładów

Funkcje pomocnicze do:
- Parsowania age group labels
- Sprawdzania overlaps w age groups
- Ekstrakcji polskich miast z tekstu
- Mapowania focus areas na branże
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


def age_group_bounds(label: str) -> tuple[int, int | None]:
    """
    Parse age group label do (min, max) bounds.

    Args:
        label: Age group label ("18-24", "25-34", "65+", etc.)

    Returns:
        Tuple (min_age, max_age) gdzie max_age może być None dla "65+"

    Example:
        >>> age_group_bounds("25-34")
        (25, 34)
        >>> age_group_bounds("65+")
        (65, None)
    """
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


def age_group_overlaps(label: str, min_age: int | None, max_age: int | None) -> bool:
    """
    Sprawdź czy age group label overlaps z podanym zakresem [min_age, max_age].

    Args:
        label: Age group label ("18-24", "25-34", etc.)
        min_age: Minimum age filter (inclusive)
        max_age: Maximum age filter (inclusive)

    Returns:
        True jeśli age group overlaps z zakresem

    Example:
        >>> age_group_overlaps("25-34", 30, 40)
        True  # Overlaps (30-34)
        >>> age_group_overlaps("18-24", 30, 40)
        False  # No overlap
    """
    group_min, group_max = age_group_bounds(label)
    if min_age is not None and group_max is not None and group_max < min_age:
        return False
    if max_age is not None and group_min is not None and group_min > max_age:
        return False
    return True


def extract_polish_cities_from_description(description: str | None) -> list[str]:
    """
    Ekstrahuj polskie miasta z tekstu description używając heurystyk.

    Rozpoznaje frazy typu:
    - "mieszkam w Warszawie"
    - "z Krakowa"
    - "pochodzę z Poznania"

    Args:
        description: Tekstowy opis (np. background_story persony)

    Returns:
        Lista rozpoznanych polskich miast

    Note:
        Używa hardcoded listy największych polskich miast do matching.
    """
    if not description:
        return []

    # Lista największych polskich miast (do rozpoznawania)
    known_cities = {
        'warszawa', 'kraków', 'wrocław', 'poznań', 'gdańsk',
        'łódź', 'katowice', 'szczecin', 'lublin', 'białystok',
        'bydgoszcz', 'gdynia', 'częstochowa', 'radom', 'toruń',
    }

    found_cities = []
    description_lower = description.lower()

    for city in known_cities:
        # Normalizuj nazwę miasta (usuń diakrytyki dla matching)
        normalized_city = unicodedata.normalize("NFKD", city)
        normalized_city = normalized_city.encode("ascii", "ignore").decode("ascii")

        # Sprawdź czy miasto występuje w tekście
        if city in description_lower or normalized_city in description_lower:
            # Kapitalizuj nazwę miasta przed zwróceniem
            found_cities.append(city.capitalize())

    return found_cities


def map_focus_area_to_industries(focus_area: str | None) -> list[str] | None:
    """
    Mapuj focus area na listę branż (industries).

    Używane przy generacji person dla focus area → industry mapping.

    Args:
        focus_area: Focus area (np. "tech", "healthcare", "finance")

    Returns:
        Lista branż lub None jeśli focus area nie jest rozpoznany/nie ma mappingu
    """
    if not focus_area:
        return None

    # Normalizuj focus area (lowercase)
    focus_area = focus_area.lower()

    # Mapowanie focus areas → industries
    focus_to_industries = {
        "tech": ["technology", "software development", "IT services", "fintech", "SaaS"],
        "healthcare": ["healthcare", "pharmaceuticals", "medical devices", "biotechnology", "health services"],
        "finance": ["banking", "financial services", "fintech", "insurance", "investment management", "accounting"],
        "education": ["education", "e-learning", "training & development", "educational technology", "academic research"],
        "retail": ["retail", "e-commerce", "consumer goods", "fashion", "FMCG"],
        "manufacturing": ["manufacturing", "industrial production", "logistics", "supply chain", "automotive"],
        "services": ["consulting", "professional services", "business services", "legal services", "HR services"],
        "entertainment": ["media & entertainment", "creative industries", "arts & culture", "gaming", "streaming"],
        "lifestyle": ["health & wellness", "fitness", "beauty", "travel & leisure", "hospitality"],
        "shopping": ["retail", "e-commerce", "consumer services", "marketplaces"],
        "general": None,  # Nie filtruj branż dla general
    }

    industries = focus_to_industries.get(focus_area)

    if industries:
        logger.info(f"🏢 Mapped focus_area='{focus_area}' → industries={industries}")

    return industries
