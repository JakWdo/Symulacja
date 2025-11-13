"""
Utilities dla systemu tagowania zasobów (Shared Context)

Obsługuje parsowanie, walidację i normalizację tagów w formacie facet:key.
Taksonomia tagów opiera się na facetach (kategoriach) i kluczach (wartościach).

Przykłady:
    - dem:age-25-34 (demografia: wiek 25-34)
    - geo:warsaw (geografia: Warszawa)
    - psy:high-openness (psychologia: wysoka otwartość)
    - biz:premium-segment (biznes: segment premium)
    - ctx:holiday-shopping (kontekst: zakupy świąteczne)
    - custom:early-adopter (niestandardowe: wczesny adopter)

Zasady:
    - Facety: whitelist (dem, geo, psy, biz, ctx, custom)
    - Klucze: kebab-case lub snake_case, lowercase, alfanumeryczne + '-' + '_'
    - Aliasy: synonimy dla kluczy (np. "warszawa" → "warsaw")
"""

import re
from typing import Dict, Optional, Tuple, List, Set


# Whitelist dozwolonych facetów (kategorii tagów)
VALID_FACETS: Set[str] = {
    "dem",      # demografia (age, gender, education, income, etc.)
    "geo",      # geografia (city, country, region)
    "psy",      # psychologia (personality traits, Big Five, Hofstede)
    "biz",      # biznes (segment, industry, company size)
    "ctx",      # kontekst (season, event, use case)
    "custom",   # niestandardowe (user-defined tags)
}

# Aliasy kluczy - mapowanie synonimów na kanoniczne wartości
# Format: {facet: {alias: canonical}}
TAG_ALIASES: Dict[str, Dict[str, str]] = {
    "geo": {
        "warszawa": "warsaw",
        "krakow": "cracow",
        "gdansk": "danzig",
        "polska": "poland",
        "pl": "poland",
    },
    "dem": {
        "m": "male",
        "f": "female",
        "k": "female",
        "mezczyzna": "male",
        "kobieta": "female",
    },
    "psy": {
        "extrovert": "extraversion",
        "introvert": "introversion",
    },
}

# Regex dla walidacji klucza (kebab-case lub snake_case)
KEY_PATTERN = re.compile(r'^[a-z0-9]+(?:[_-][a-z0-9]+)*$')


class TagValidationError(ValueError):
    """Błąd walidacji tagu."""
    pass


def parse_tag(tag: str) -> Tuple[str, str]:
    """
    Parsuje tag w formacie "facet:key" na tuple (facet, key).

    Args:
        tag: String w formacie "facet:key" (np. "dem:age-25-34")

    Returns:
        Tuple (facet, key)

    Raises:
        TagValidationError: Jeśli tag nie ma formatu "facet:key"

    Examples:
        >>> parse_tag("dem:age-25-34")
        ('dem', 'age-25-34')
        >>> parse_tag("geo:warsaw")
        ('geo', 'warsaw')
        >>> parse_tag("invalid")  # Brak ':'
        TagValidationError: Tag must be in format 'facet:key', got: invalid
    """
    if ':' not in tag:
        raise TagValidationError(f"Tag must be in format 'facet:key', got: {tag}")

    parts = tag.split(':', 1)
    if len(parts) != 2:
        raise TagValidationError(f"Tag must have exactly one ':' separator, got: {tag}")

    facet, key = parts[0].strip(), parts[1].strip()

    if not facet or not key:
        raise TagValidationError(f"Both facet and key must be non-empty, got: {tag}")

    return facet, key


def normalize_tag(tag: str, apply_aliases: bool = True) -> str:
    """
    Normalizuje tag do kanonicznej formy.

    Normalizacja obejmuje:
    - Lowercase
    - Trim whitespace
    - Aplikację aliasów (jeśli apply_aliases=True)

    Args:
        tag: Tag w formacie "facet:key"
        apply_aliases: Czy zastosować mapowanie aliasów

    Returns:
        Znormalizowany tag w formacie "facet:key"

    Raises:
        TagValidationError: Jeśli tag jest niepoprawny

    Examples:
        >>> normalize_tag("DEM:AGE-25-34")
        'dem:age-25-34'
        >>> normalize_tag("geo:Warszawa")  # Alias: warszawa → warsaw
        'geo:warsaw'
        >>> normalize_tag("geo:warszawa", apply_aliases=False)
        'geo:warszawa'
    """
    # Parse i lowercase
    facet, key = parse_tag(tag)
    facet = facet.lower()
    key = key.lower()

    # Aplikuj aliasy jeśli włączone
    if apply_aliases and facet in TAG_ALIASES:
        key = TAG_ALIASES[facet].get(key, key)

    return f"{facet}:{key}"


def validate_facet(facet: str) -> None:
    """
    Waliduje facet (kategorię tagu).

    Args:
        facet: Facet do walidacji

    Raises:
        TagValidationError: Jeśli facet nie jest na whiteliście

    Examples:
        >>> validate_facet("dem")  # OK
        >>> validate_facet("invalid")
        TagValidationError: Invalid facet 'invalid'. Allowed: dem, geo, psy, biz, ctx, custom
    """
    if facet not in VALID_FACETS:
        allowed = ", ".join(sorted(VALID_FACETS))
        raise TagValidationError(
            f"Invalid facet '{facet}'. Allowed: {allowed}"
        )


def validate_key(key: str) -> None:
    """
    Waliduje klucz tagu (wartość).

    Klucz musi być w formacie kebab-case lub snake_case:
    - Lowercase alfanumeryczne znaki
    - Opcjonalnie separatory '-' lub '_'
    - Nie może zaczynać/kończyć się separatorem

    Args:
        key: Klucz do walidacji

    Raises:
        TagValidationError: Jeśli klucz nie spełnia wymogów

    Examples:
        >>> validate_key("age-25-34")  # OK
        >>> validate_key("high_openness")  # OK
        >>> validate_key("Age-25-34")  # Uppercase nie dozwolone
        TagValidationError: Key must be lowercase kebab-case or snake_case...
        >>> validate_key("-invalid")  # Zaczyna się separatorem
        TagValidationError: Key must be lowercase kebab-case or snake_case...
    """
    if not KEY_PATTERN.match(key):
        raise TagValidationError(
            f"Key must be lowercase kebab-case or snake_case (alphanumeric + '-' or '_'), "
            f"got: '{key}'"
        )


def validate_tag(tag: str, apply_aliases: bool = True) -> str:
    """
    Waliduje i normalizuje tag.

    Kombinuje parsowanie, normalizację i walidację w jeden krok.
    Zwraca znormalizowany tag jeśli walidacja przeszła.

    Args:
        tag: Tag do walidacji (format "facet:key")
        apply_aliases: Czy zastosować aliasy podczas normalizacji

    Returns:
        Znormalizowany i zwalidowany tag

    Raises:
        TagValidationError: Jeśli tag jest niepoprawny

    Examples:
        >>> validate_tag("DEM:age-25-34")
        'dem:age-25-34'
        >>> validate_tag("geo:Warszawa")
        'geo:warsaw'
        >>> validate_tag("invalid:UPPERCASE-KEY")
        TagValidationError: Key must be lowercase...
        >>> validate_tag("invalid_facet:key")
        TagValidationError: Invalid facet 'invalid_facet'...
    """
    # Normalizacja (parsuje i lowercase)
    normalized = normalize_tag(tag, apply_aliases=apply_aliases)

    # Parse znormalizowanego tagu
    facet, key = parse_tag(normalized)

    # Walidacja facetu
    validate_facet(facet)

    # Walidacja klucza
    validate_key(key)

    return normalized


def parse_tag_list(tags: str, separator: str = ",") -> List[str]:
    """
    Parsuje listę tagów oddzielonych separatorem.

    Args:
        tags: String z tagami oddzielonymi separatorem
        separator: Separator (domyślnie ',')

    Returns:
        Lista znormalizowanych i zwalidowanych tagów

    Raises:
        TagValidationError: Jeśli którykolwiek tag jest niepoprawny

    Examples:
        >>> parse_tag_list("dem:age-25-34, geo:warsaw, psy:high-openness")
        ['dem:age-25-34', 'geo:warsaw', 'psy:high-openness']
        >>> parse_tag_list("dem:age-25-34|geo:warsaw", separator="|")
        ['dem:age-25-34', 'geo:warsaw']
    """
    if not tags or not tags.strip():
        return []

    tag_list = [tag.strip() for tag in tags.split(separator)]
    validated = [validate_tag(tag) for tag in tag_list if tag]

    return validated


def get_facet_from_tag(tag: str) -> str:
    """
    Ekstrahuje facet z tagu.

    Args:
        tag: Tag w formacie "facet:key"

    Returns:
        Facet (kategoria)

    Examples:
        >>> get_facet_from_tag("dem:age-25-34")
        'dem'
        >>> get_facet_from_tag("geo:warsaw")
        'geo'
    """
    facet, _ = parse_tag(tag)
    return facet.lower()


def get_key_from_tag(tag: str) -> str:
    """
    Ekstrahuje klucz z tagu.

    Args:
        tag: Tag w formacie "facet:key"

    Returns:
        Klucz (wartość)

    Examples:
        >>> get_key_from_tag("dem:age-25-34")
        'age-25-34'
        >>> get_key_from_tag("geo:warsaw")
        'warsaw'
    """
    _, key = parse_tag(tag)
    return key.lower()


def group_tags_by_facet(tags: List[str]) -> Dict[str, List[str]]:
    """
    Grupuje tagi według facetów.

    Args:
        tags: Lista tagów w formacie "facet:key"

    Returns:
        Dict {facet: [key1, key2, ...]}

    Examples:
        >>> group_tags_by_facet(["dem:age-25-34", "dem:male", "geo:warsaw"])
        {'dem': ['age-25-34', 'male'], 'geo': ['warsaw']}
    """
    grouped: Dict[str, List[str]] = {}

    for tag in tags:
        facet = get_facet_from_tag(tag)
        key = get_key_from_tag(tag)

        if facet not in grouped:
            grouped[facet] = []

        grouped[facet].append(key)

    return grouped


def is_valid_tag(tag: str) -> bool:
    """
    Sprawdza czy tag jest poprawny (bez rzucania wyjątku).

    Args:
        tag: Tag do sprawdzenia

    Returns:
        True jeśli tag jest poprawny, False w przeciwnym razie

    Examples:
        >>> is_valid_tag("dem:age-25-34")
        True
        >>> is_valid_tag("invalid")
        False
        >>> is_valid_tag("invalid_facet:key")
        False
    """
    try:
        validate_tag(tag)
        return True
    except TagValidationError:
        return False
