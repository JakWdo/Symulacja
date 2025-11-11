"""
NLP Constants for Polish and English language support.

Contains stopwords, sentiment keywords, and suffix patterns for text analysis.
"""

import logging

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
# Try to load NLTK stopwords, fallback to hardcoded list if not available
try:
    import nltk
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

# Comprehensive Polish stopwords (custom + NLTK)
POLISH_STOPWORDS_CUSTOM = {
    # Pronouns
    "ja", "ty", "on", "ona", "ono", "my", "wy", "oni", "one",
    "mnie", "cię", "go", "ją", "nas", "was", "ich", "sobie", "się",
    "moja", "mój", "moje", "twoja", "twój", "twoje", "jego", "jej",
    # Prepositions
    "w", "z", "do", "od", "na", "po", "o", "u", "przy", "przez",
    "za", "dla", "nad", "pod", "przed", "między", "bez",
    # Conjunctions
    "i", "a", "ale", "oraz", "czy", "że", "jeśli", "gdyby", "bo",
    "więc", "zatem", "jednak", "ponieważ", "dlatego",
    # Verbs (common forms)
    "jest", "są", "był", "była", "było", "byli", "były", "być",
    "mieć", "ma", "mają", "miał", "miała", "miało", "mieli", "miały",
    "może", "mogą", "mógł", "mogła", "mogło", "mogli", "mogły",
    "chce", "chcą", "chciał", "chciała", "chciało", "chcieli", "chciały",
    "wie", "wiedzą", "wiedział", "wiedziała", "wiedziało", "wiedzieli", "wiedziały",
    # Articles & particles
    "ten", "ta", "to", "te", "ci", "tego", "tej", "tych",
    "jeden", "jedna", "jedno", "jedni", "jedne",
    "żaden", "żadna", "żadne", "żadni", "żadne",
    "każdy", "każda", "każde", "wszyscy", "wszystkie",
    "który", "która", "które", "którzy", "których",
    "jaki", "jaka", "jakie", "jacy", "jakich",
    "taki", "taka", "takie", "tacy", "takich",
    "ile", "ilu", "gdzie", "kiedy", "jak", "dlaczego", "czemu",
    # Adverbs
    "tu", "tutaj", "tam", "tu", "teraz", "wtedy", "zawsze", "nigdy",
    "często", "rzadko", "czasami", "bardzo", "mało", "dużo", "zbyt",
    "bardziej", "mniej", "najbardziej", "najmniej", "też", "także", "również",
    # Common verbs (infinitive)
    "robić", "zrobić", "mówić", "powiedzieć", "iść", "pójść",
    # Numbers
    "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć", "dziesięć",
    # Common words that appear in concepts but are not meaningful
    "brak", "czas", "czasu", "czasów", "razy", "rok", "roku", "lat",
    "sposób", "sposób", "sposobu", "sposobów", "rzecz", "rzeczy",
    "część", "części", "miejsce", "miejsca", "dane", "danych",
    "np", "itp", "itd", "tzn", "tj", "tzw",
}

# English stopwords (basic set + common words)
ENGLISH_STOPWORDS_CUSTOM = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "may", "might", "can", "this", "that", "these", "those",
    "it", "its", "he", "she", "they", "them", "their", "his", "her",
    "from", "as", "not", "all", "any", "some", "such", "no", "yes",
    "more", "most", "less", "very", "so", "just", "than", "too",
    "there", "here", "when", "where", "why", "how", "what", "which",
}

# Combine all stopwords
POLISH_STOPWORDS = POLISH_STOPWORDS_CUSTOM | POLISH_STOPWORDS_NLTK
ENGLISH_STOPWORDS = ENGLISH_STOPWORDS_CUSTOM | ENGLISH_STOPWORDS_NLTK
ALL_STOPWORDS = POLISH_STOPWORDS | ENGLISH_STOPWORDS

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
