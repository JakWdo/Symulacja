"""
Language detection and text normalization utilities.

Provides heuristic language detection for Polish/English texts
and pseudo-lemmatization for Polish words.
"""

import logging
import re

from .constants import POLISH_SUFFIXES

logger = logging.getLogger(__name__)


def detect_input_language(text: str) -> str:
    """
    Wykrywa język z tekstu input (prosty heurystyczny detektor).

    Algorytm:
    1. Zlicza wystąpienia polskich stopwords (jak, co, jest, się, czy, ...)
    2. Zlicza wystąpienia angielskich stopwords (what, how, is, are, ...)
    3. Porównuje liczności i wybiera język z większą liczbą trafień
    4. Fallback: polski (domyślny język produktu)

    Args:
        text: Tekst do analizy (questions/messages z focus group)

    Returns:
        'pl' lub 'en'

    Note:
        To jest prosty heurystyczny detektor. W przyszłości można użyć biblioteki
        jak langdetect, ale dla dwóch języków (pl/en) ta metoda jest wystarczająca.

    Examples:
        >>> detect_input_language("Jak oceniasz ten produkt?")
        'pl'
        >>> detect_input_language("What do you think about this product?")
        'en'
        >>> detect_input_language("xyz123")  # unclear text
        'pl'
    """
    # Polski stopwords (niektóre z listy POLISH_STOPWORDS)
    polish_indicators = [
        'jak', 'co', 'jest', 'się', 'czy', 'nie', 'ale', 'to', 'że', 'do',
        'z', 'na', 'i', 'w', 'o', 'dla', 'po', 'przez', 'od', 'kiedy',
        'dlaczego', 'gdzie', 'który', 'jakie', 'jaką', 'jaką', 'które',
        'czym', 'czemu', 'kto', 'kim', 'kogo', 'was', 'nas', 'mnie', 'cię',
        'możesz', 'możemy', 'powinien', 'powinna', 'powinno', 'chcesz',
        'chcemy', 'myślisz', 'uważasz', 'uważam', 'myślę', 'sądzisz',
    ]

    # Anglojęzyczne stopwords
    english_indicators = [
        'what', 'how', 'why', 'where', 'when', 'who', 'which', 'is', 'are',
        'the', 'and', 'but', 'that', 'this', 'with', 'for', 'from', 'about',
        'would', 'should', 'could', 'have', 'has', 'do', 'does', 'did',
        'your', 'you', 'we', 'they', 'them', 'think', 'believe', 'feel',
        'can', 'will', 'must', 'may', 'might',
    ]

    text_lower = text.lower()
    # Usuń znaki interpunkcyjne i podziel na słowa
    words = re.findall(r'\b[a-ząćęłńóśźż]+\b', text_lower, flags=re.UNICODE)

    # Zlicz dokładne dopasowania słów kluczowych (nie substrings!)
    polish_count = sum(1 for word in words if word in polish_indicators)
    english_count = sum(1 for word in words if word in english_indicators)

    logger.debug(f"Language detection: PL={polish_count}, EN={english_count} (sample: {text[:100]}...)")

    # Jeśli więcej polskich słów → polski
    if polish_count > english_count:
        return 'pl'
    # Jeśli więcej angielskich słów → angielski
    elif english_count > polish_count:
        return 'en'

    # Default: polski (dla polskiego produktu)
    return 'pl'


def normalize_polish_word(word: str) -> str:
    """
    Pseudo-lematyzacja dla polskich słów.

    Usuwa najczęstsze końcówki fleksyjne, aby zredukować warianty tego samego słowa.
    UWAGA: To bardzo prosta heurystyka, nie zastępuje prawdziwej lematyzacji.

    Args:
        word: Słowo do normalizacji

    Returns:
        Znormalizowane słowo
    """
    word = word.lower()

    # Skip very short words
    if len(word) <= 3:
        return word

    # Try removing common suffixes
    for suffix in POLISH_SUFFIXES:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            # Keep at least 3 characters after removing suffix
            normalized = word[:-len(suffix)]
            if len(normalized) >= 3:
                return normalized

    return word
