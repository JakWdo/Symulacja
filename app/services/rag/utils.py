"""Wspólne utility functions dla RAG services.

Ten moduł zawiera funkcje pomocnicze używane przez wiele serwisów RAG:
- escape_lucene_query() - Escapowanie znaków specjalnych Lucene dla Neo4j fulltext search
"""


def escape_lucene_query(query: str) -> str:
    """Escapuje znaki specjalne Lucene w zapytaniu fulltext dla Neo4j.

    Lucene special characters wymagające escapowania:
    + - && || ! ( ) { } [ ] ^ " ~ * ? : \\ /

    Ta funkcja jest używana przed wysłaniem query do db.index.fulltext.queryNodes()
    aby zapobiec błędom parsowania Lucene (np. "Lexical error" dla znaków `/`, `-`).

    Args:
        query: Surowe zapytanie (np. "mężczyzna 18-24 Poznań wyższe / średnie")

    Returns:
        Bezpieczny string z escapowanymi znakami specjalnymi
        (np. "mężczyzna 18\\-24 Poznań wyższe \\/ średnie")

    Example:
        >>> escape_lucene_query("18-24 studia / pierwsza praca")
        '18\\-24 studia \\/ pierwsza praca'
    """
    if not query:
        return ""

    # Lucene special characters - muszą być poprzedzone backslash
    special_chars = {"+", "-", "&", "|", "!", "(", ")", "{", "}", "[", "]",
                    "^", '"', "~", "*", "?", ":", "\\", "/"}

    # Escapuj znak po znaku, normalizuj newlines
    escaped_chars: list[str] = []
    for ch in query.replace("\n", " "):
        if ch in special_chars:
            escaped_chars.append("\\" + ch)
        else:
            escaped_chars.append(ch)

    # Normalizuj wielokrotne spacje
    safe = " ".join("".join(escaped_chars).split())
    return safe
