"""
NLP utilities for focus group analysis.

This module provides natural language processing utilities for Polish and English:
- Language detection
- Sentiment analysis
- Concept extraction
- Stopwords and constants
"""

from .constants import (
    POLISH_STOPWORDS,
    ENGLISH_STOPWORDS,
    POSITIVE_KEYWORDS_PL,
    NEGATIVE_KEYWORDS_PL,
    POLISH_SUFFIXES,
)
from .language_detection import detect_input_language, normalize_polish_word
from .sentiment_analysis import simple_sentiment_score
from .concept_extraction import extract_concepts

__all__ = [
    "POLISH_STOPWORDS",
    "ENGLISH_STOPWORDS",
    "POSITIVE_KEYWORDS_PL",
    "NEGATIVE_KEYWORDS_PL",
    "POLISH_SUFFIXES",
    "detect_input_language",
    "normalize_polish_word",
    "simple_sentiment_score",
    "extract_concepts",
]
