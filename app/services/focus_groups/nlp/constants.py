"""
NLP Constants for Polish and English language support.

Contains stopwords, sentiment keywords, and suffix patterns for text analysis.
"""

import logging
from config.stopwords_loader import get_polish_stopwords, get_english_stopwords

logger = logging.getLogger(__name__)

# Sentiment Keywords
# ==================
# Positive words for sentiment analysis (English)
POSITIVE_KEYWORDS_EN = {
    "good", "great", "excellent", "love", "like", "enjoy", "positive",
    "amazing", "wonderful", "fantastic", "best", "happy", "yes", "agree",
    "excited", "helpful", "valuable", "useful"
}

# Negative words for sentiment analysis (English)
NEGATIVE_KEYWORDS_EN = {
    "bad", "terrible", "hate", "dislike", "awful", "worst", "negative",
    "horrible", "poor", "no", "disagree", "concern", "worried", "against",
    "confusing", "hard", "difficult"
}

# Polish sentiment keywords (extend as needed)
POSITIVE_KEYWORDS_PL = {
    "dobry", "dobra", "dobre", "świetny", "świetna", "świetne", "doskonały",
    "doskonała", "doskonałe", "kocham", "lubię", "podoba", "pozytywny",
    "pozytywna", "pozytywne", "wspaniały", "wspaniała", "wspaniałe",
    "najlepszy", "najlepsza", "najlepsze", "szczęśliwy", "tak", "zgadzam",
    "pomocny", "pomocna", "pomocne", "wartościowy", "przydatny"
}

NEGATIVE_KEYWORDS_PL = {
    "zły", "zła", "złe", "okropny", "okropna", "okropne", "nienawidzę",
    "nie lubię", "nie podoba", "negatywny", "negatywna", "negatywne",
    "najgorszy", "najgorsza", "najgorsze", "słaby", "słaba", "słabe",
    "nie", "nie zgadzam", "obawa", "martwy", "przeciw", "trudny", "trudna",
    "trudne", "ciężki", "ciężka", "ciężkie"
}

# Polish NLP Support - Stopwords
# ==============================
# Load stopwords from centralized config/prompts/shared/stopwords.yaml
# This avoids duplication and ensures consistency across the codebase

# Try to load NLTK stopwords as supplementary (if available)
try:
    import nltk  # noqa: F401 - używany w try/except do sprawdzenia dostępności
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    try:
        POLISH_STOPWORDS_NLTK = set(stopwords.words('polish'))
        ENGLISH_STOPWORDS_NLTK = set(stopwords.words('english'))
    except LookupError:
        # NLTK data not downloaded - NLTK dependency removed
        logger.warning("NLTK stopwords data not found (NLTK dependency removed)")
        NLTK_AVAILABLE = False
        POLISH_STOPWORDS_NLTK = set()
        ENGLISH_STOPWORDS_NLTK = set()
except ImportError:
    NLTK_AVAILABLE = False
    POLISH_STOPWORDS_NLTK = set()
    ENGLISH_STOPWORDS_NLTK = set()

# Load stopwords from centralized YAML (primary source)
POLISH_STOPWORDS_YAML = get_polish_stopwords()
ENGLISH_STOPWORDS_YAML = get_english_stopwords()

# Combine YAML stopwords with NLTK (if available) for maximum coverage
POLISH_STOPWORDS = POLISH_STOPWORDS_YAML | POLISH_STOPWORDS_NLTK
ENGLISH_STOPWORDS = ENGLISH_STOPWORDS_YAML | ENGLISH_STOPWORDS_NLTK
ALL_STOPWORDS = POLISH_STOPWORDS | ENGLISH_STOPWORDS

logger.debug(
    f"Loaded stopwords: {len(POLISH_STOPWORDS)} Polish, "
    f"{len(ENGLISH_STOPWORDS)} English (YAML + NLTK)"
)

# Polish suffix patterns for pseudo-lemmatization
POLISH_SUFFIXES = [
    # Genitive plural
    "ów", "ami", "ach",
    # Adjective endings
    "ego", "ymi", "ymi", "owej", "owych",
    # Common verb endings
    "ać", "ić", "yć", "eć",
    # Common noun endings
    "ami", "ach", "iej",
]
