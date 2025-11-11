"""
Concept extraction utilities for Polish and English text.

Extracts key concepts and multi-word phrases using n-gram analysis
and frequency-based filtering.
"""

import logging
import re
from collections import Counter

from sklearn.feature_extraction.text import CountVectorizer

from .constants import ALL_STOPWORDS
from .language_detection import normalize_polish_word

logger = logging.getLogger(__name__)


def extract_concepts(text: str, min_frequency: int = 2, max_concepts: int = 15) -> list[str]:
    """
    Ekstrakcja kluczowych koncepcji z tekstu z wsparciem dla języka polskiego.

    Wykorzystuje:
    - Polskie i angielskie stopwords (NLTK + custom)
    - Regex z polskimi znakami (ą, ć, ę, ł, ń, ó, ś, ź, ż)
    - Pseudo-lematyzację (usuwanie końcówek fleksyjnych)
    - N-gramy (bigramy i trigramy) z sklearn CountVectorizer
    - Preferencję dla fraz wielowyrazowych nad pojedynczymi słowami

    Args:
        text: Tekst do analizy
        min_frequency: Minimalna liczba wystąpień n-grama (domyślnie 2)
        max_concepts: Maksymalna liczba koncepcji do zwrócenia (domyślnie 15)

    Returns:
        Lista top koncepcji, posortowanych według częstości
    """
    if not text or len(text.strip()) < 10:
        return []

    text_lower = text.lower()

    # Step 1: Extract unigrams with Polish character support
    # Regex: 3+ characters, Polish diacritics, hyphens for compound words
    unigram_pattern = r'\b[a-ząćęłńóśźż-]{3,}\b'
    words = re.findall(unigram_pattern, text_lower, flags=re.UNICODE)

    # Filter stopwords and normalize
    normalized_words = []
    for word in words:
        # Skip stopwords
        if word in ALL_STOPWORDS:
            continue
        # Skip pure numbers or very short words
        if word.isdigit() or len(word) < 3:
            continue
        # Normalize (pseudo-lemmatization)
        normalized = normalize_polish_word(word)
        if normalized not in ALL_STOPWORDS:
            normalized_words.append(normalized)

    # Count unigrams
    unigram_counts = Counter(normalized_words)

    # Step 2: Extract n-grams (bigrams and trigrams) using sklearn
    # This catches multi-word concepts like "customer experience", "product quality"
    ngram_concepts = []
    try:
        # Create vectorizer with n-gram support
        vectorizer = CountVectorizer(
            ngram_range=(2, 3),  # Bigrams and trigrams
            min_df=1,  # Minimum document frequency
            max_df=0.9,  # Maximum document frequency (filter very common)
            stop_words=list(ALL_STOPWORDS),
            token_pattern=r'\b[a-ząćęłńóśźż-]{3,}\b',  # Polish characters
            lowercase=True,
        )

        # Fit and transform text (treat as single document)
        X = vectorizer.fit_transform([text_lower])

        # Get n-grams with their counts
        feature_names = vectorizer.get_feature_names_out()
        counts = X.toarray()[0]

        # Filter n-grams: only those with ≥min_frequency occurrences
        for ngram, count in zip(feature_names, counts):
            if count >= min_frequency:
                ngram_concepts.append((ngram, count))

        # Sort by frequency
        ngram_concepts.sort(key=lambda x: x[1], reverse=True)

    except Exception as e:
        # If sklearn extraction fails, continue with unigrams only
        logger.warning(f"N-gram extraction failed: {e}")
        ngram_concepts = []

    # Step 3: Combine and prioritize n-grams
    # Strategy: Prefer n-grams (multi-word concepts) over single words
    final_concepts = []

    # Add top n-grams first (up to 10)
    for ngram, count in ngram_concepts[:10]:
        final_concepts.append(ngram)

    # Add top unigrams to fill remaining slots
    # Skip unigrams that are already part of extracted n-grams
    ngram_words = set()
    for ngram, _ in ngram_concepts:
        ngram_words.update(ngram.split())

    for word, count in unigram_counts.most_common(30):
        # Skip if already in final concepts
        if word in final_concepts:
            continue
        # Skip if word is part of an n-gram we already included
        if word in ngram_words:
            continue
        # Add if we have slots remaining
        if len(final_concepts) < max_concepts:
            final_concepts.append(word)
        else:
            break

    # If we don't have enough concepts, add more unigrams
    if len(final_concepts) < 10:
        for word, count in unigram_counts.most_common(max_concepts):
            if word not in final_concepts and len(final_concepts) < max_concepts:
                final_concepts.append(word)

    return final_concepts[:max_concepts]
