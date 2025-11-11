"""
Sentiment analysis utilities for Polish and English text.

Provides simple keyword-based sentiment scoring.
"""

from .constants import POSITIVE_KEYWORDS_EN, NEGATIVE_KEYWORDS_EN, POSITIVE_KEYWORDS_PL, NEGATIVE_KEYWORDS_PL


def simple_sentiment_score(text: str) -> float:
    """
    Prosta analiza sentymentu na podstawie słów kluczowych.

    Algorytm:
    1. Liczy wystąpienia słów pozytywnych (POSITIVE_KEYWORDS)
    2. Liczy wystąpienia słów negatywnych (NEGATIVE_KEYWORDS)
    3. Oblicza score = (pozytywne - negatywne) / wszystkie

    Args:
        text: Tekst do analizy

    Returns:
        Wartość od -1.0 (czysto negatywny) do 1.0 (czysto pozytywny)
        0.0 = neutralny lub brak słów kluczowych
    """
    lowered = text.lower()

    # Combine all positive/negative keywords (PL + EN)
    all_positive = POSITIVE_KEYWORDS_EN | POSITIVE_KEYWORDS_PL
    all_negative = NEGATIVE_KEYWORDS_EN | NEGATIVE_KEYWORDS_PL

    # Count occurrences
    pos = sum(1 for token in all_positive if token in lowered)
    neg = sum(1 for token in all_negative if token in lowered)
    total = pos + neg

    if total == 0:
        return 0.0

    return float((pos - neg) / total)
