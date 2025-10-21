"""
Schemy dla Segment Brief - opisów segmentów społecznych.

SegmentBrief jest wspólny dla wszystkich person w danym segmencie
(tym samym wieku, wykształceniu, lokalizacji, etc.) i jest cachowany w Redis.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class SegmentBrief(BaseModel):
    """
    Brief segmentu społecznego - długi, ciekawy opis grupy demograficznej.

    Ten brief jest wspólny dla wszystkich person w segmencie i bazuje na:
    - Demografii segmentu (wiek, płeć, wykształcenie, lokalizacja, dochód)
    - RAG knowledge (dane o polskim społeczeństwie)
    - Przykładowych personach z tego segmentu (jeśli istnieją)

    Brief jest cachowany w Redis (TTL 7 dni) z kluczem:
    `segment_brief:{project_id}:{segment_id}`

    gdzie segment_id = hash(age, education, location, gender, income)
    """

    segment_id: str = Field(
        description="Hash ID segmentu (np. 'seg_25-34_wyższe_warszawa_kobieta')"
    )

    segment_name: str = Field(
        description="Mówiąca nazwa segmentu (np. 'Młodzi Prekariusze', 'Aspirujące Profesjonalistki 35-44')"
    )

    description: str = Field(
        description="Długi (400-800 słów), ciekawy, personalny opis segmentu - storytelling approach"
    )

    social_context: str = Field(
        description="Kontekst społeczno-ekonomiczny segmentu (300-500 słów)"
    )

    characteristics: list[str] = Field(
        default_factory=list,
        description="5-7 kluczowych cech segmentu (np. 'Profesjonaliści z wielkich miast')"
    )

    based_on_personas_count: int = Field(
        default=0,
        description="Liczba person użytych jako przykłady przy generowaniu briefu"
    )

    demographics: dict = Field(
        default_factory=dict,
        description="Demografia segmentu: age, gender, education, location, income"
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp generacji briefu"
    )

    generated_by: str = Field(
        default="gemini-2.5-pro",
        description="Model LLM użyty do generacji"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "segment_id": "seg_25-34_wyższe_warszawa_kobieta",
                "segment_name": "Aspirujące Profesjonalistki 25-34",
                "description": "Wiktor ma 29 lat i właśnie skończył historię sztuki na UAM...",
                "social_context": "Segment charakteryzuje się wysoką mobilnością zawodową...",
                "characteristics": [
                    "Profesjonaliści z wielkich miast",
                    "Wysokie wykształcenie",
                    "Stabilna kariera",
                    "Early adopters technologii"
                ],
                "based_on_personas_count": 3,
                "demographics": {
                    "age": "25-34",
                    "gender": "kobieta",
                    "education": "wyższe",
                    "location": "Warszawa",
                    "income": "7 500 - 10 000 zł"
                },
                "generated_at": "2025-10-16T14:30:00Z",
                "generated_by": "gemini-2.5-pro"
            }
        }


class PersonaUniqueness(BaseModel):
    """
    Opis unikalności persony w kontekście jej segmentu.

    Generowany dla każdej persony indywidualnie, wyjaśnia czym ta osoba
    się wyróżnia spośród typowych przedstawicieli segmentu.

    Używany w sekcji "Dlaczego ta osoba jest wyjątkowa" w panelu persona details.
    """

    persona_id: str = Field(
        description="UUID persony"
    )

    segment_id: str = Field(
        description="ID segmentu do którego należy persona"
    )

    uniqueness_description: str = Field(
        description="2-4 zdania o tym, czym ta osoba wyróżnia się w swoim segmencie"
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    class Config:
        json_schema_extra = {
            "example": {
                "persona_id": "uuid-here",
                "segment_id": "seg_25-34_wyższe_warszawa",
                "uniqueness_description": "Wiktor wyróżnia się w grupie Młodych Prekariuszy swoją determinacją do pozostania w sektorze kultury pomimo finansowych trudności. Podczas gdy wielu jego rówieśników z wykształceniem humanistycznym przeszło do korporacji dla stabilności, on świadomie wybiera niższe zarobki za możliwość pracy z tym, co kocha.",
                "generated_at": "2025-10-16T14:30:00Z"
            }
        }


class SegmentBriefRequest(BaseModel):
    """Request schema dla generowania segment brief."""

    demographics: dict = Field(
        description="Demografia segmentu: age, gender, education, location, income"
    )

    project_id: str = Field(
        description="UUID projektu"
    )

    max_example_personas: int = Field(
        default=3,
        description="Maksymalna liczba przykładowych person do użycia w generacji"
    )

    force_refresh: bool = Field(
        default=False,
        description="Czy wymusić regenerację (ominąć cache)"
    )


class SegmentBriefResponse(BaseModel):
    """Response schema dla segment brief."""

    brief: SegmentBrief = Field(
        description="Wygenerowany lub pobrany z cache brief segmentu"
    )

    from_cache: bool = Field(
        description="Czy brief został pobrany z cache (True) czy wygenerowany na żywo (False)"
    )

    cache_ttl_seconds: int | None = Field(
        default=None,
        description="Pozostały TTL w cache (jeśli from_cache=True)"
    )
