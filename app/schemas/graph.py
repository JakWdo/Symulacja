"""
Schematy Pydantic dla API analizy grafowej
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Node w grafie wiedzy"""
    id: str = Field(..., description="Unikalny identyfikator node")
    name: str = Field(..., description="Nazwa wyświetlana")
    type: str = Field(..., description="Typ: persona, concept, emotion")
    group: int = Field(..., description="Grupa dla kolorowania (1=persona, 2=concept, 3=emotion)")
    size: int = Field(..., description="Rozmiar node (proporcjonalny do ważności)")
    sentiment: Optional[float] = Field(None, description="Sentiment score (-1.0 do 1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Dodatkowe dane")


class GraphLink(BaseModel):
    """Połączenie między nodes w grafie"""
    source: str = Field(..., description="ID źródłowego node")
    target: str = Field(..., description="ID docelowego node")
    type: str = Field(..., description="Typ relacji: mentions, agrees, disagrees, feels")
    strength: float = Field(..., description="Siła połączenia (0.0-1.0)")
    sentiment: Optional[float] = Field(None, description="Sentiment (dla MENTIONS)")


class GraphDataResponse(BaseModel):
    """Pełne dane grafu dla wizualizacji"""
    nodes: List[GraphNode] = Field(..., description="Lista wszystkich nodes")
    links: List[GraphLink] = Field(..., description="Lista wszystkich connections")


class GraphStatsResponse(BaseModel):
    """Statystyki budowania grafu"""
    personas_added: int = Field(..., description="Liczba dodanych person")
    concepts_extracted: int = Field(..., description="Liczba wyekstraktowanych konceptów")
    relationships_created: int = Field(..., description="Liczba utworzonych relacji")
    emotions_created: int = Field(..., description="Liczba dodanych emocji")


class InfluentialPersona(BaseModel):
    """Wpływowa persona w grafie"""
    id: str
    name: str
    influence: int = Field(..., description="Wskaźnik wpływu (0-100)")
    connections: int = Field(..., description="Liczba połączeń")
    sentiment: float = Field(..., description="Średni sentiment")


class InfluentialPersonasResponse(BaseModel):
    """Lista najbardziej wpływowych person"""
    personas: List[InfluentialPersona]


class KeyConcept(BaseModel):
    """Kluczowy koncept z dyskusji"""
    name: str
    frequency: int = Field(..., description="Liczba wzmianek")
    sentiment: float = Field(..., description="Średni sentiment")
    personas: List[str] = Field(..., description="Lista person wspominających")


class KeyConceptsResponse(BaseModel):
    """Lista kluczowych konceptów"""
    concepts: List[KeyConcept]


class GraphQueryInsight(BaseModel):
    """Pojedynczy insight zwrócony przez zapytanie"""
    title: str
    detail: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphQueryRequest(BaseModel):
    """Zapytanie natural language do analizy grafu"""
    question: str = Field(..., min_length=1, max_length=500, description="Pytanie użytkownika")


class GraphQueryResponse(BaseModel):
    """Ustrukturyzowana odpowiedź na zapytanie"""
    answer: str
    insights: List[GraphQueryInsight] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
