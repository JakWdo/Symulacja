"""Narzędzia do sanityzacji zapytań Lucene fulltext search.

Moduł odpowiada za escape znaków specjalnych Lucene aby uniknąć błędów
CypherSyntaxError i TokenMgrError podczas wyszukiwania pełnotekstowego.
"""

import logging
import re

logger = logging.getLogger(__name__)


def sanitize_lucene_query(query: str) -> str:
    """Sanityzuje query dla Lucene fulltext search - escape znaków specjalnych.

    Lucene special characters wymagające escapowania: / ( ) [ ] { } \ " ' + - * ? : ~ ^
    Używamy whitelist approach - escapujemy tylko znane problematyczne znaki.

    Args:
        query: Oryginalny query string

    Returns:
        Sanitized query bezpieczny dla Lucene parser
    """
    # Lista znaków specjalnych Lucene wymagających escapowania
    # Źródło: https://lucene.apache.org/core/8_0_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html
    lucene_special_chars = [
        '/', '(', ')', '[', ']', '{', '}',
        '\\', '"', "'", '+', '-', '*', '?', ':', '~', '^'
    ]

    sanitized = query
    for char in lucene_special_chars:
        # Escape each special char with backslash
        # Double backslash for Python string literal
        sanitized = sanitized.replace(char, f'\\{char}')

    # Dodatkowo: usuń wielokrotne spacje (cleanup)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # Log jeśli query został zmieniony (debugging)
    if sanitized != query:
        logger.debug(
            "Lucene query sanitized: '%s' → '%s'",
            query[:100],
            sanitized[:100]
        )

    return sanitized
