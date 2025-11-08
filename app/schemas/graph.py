"""
Schematy Pydantic dla API analizy grafowej
"""

from pydantic import BaseModel, Field

from app.types import JSONObject


class NodeProperties(BaseModel):
    """Bogate metadane węzła w grafie wiedzy"""
    description: str | None = Field(None, description="Szczegółowy opis kontekstu (2-3 zdania)")
    summary: str | None = Field(None, description="Jednozdaniowe podsumowanie")
    key_facts: str | None = Field(None, description="Lista kluczowych faktów (oddzielone średnikami)")
    time_period: str | None = Field(None, description="Okres czasu (YYYY lub YYYY-YYYY)")
    magnitude: str | None = Field(None, description="Wielkość/skala z jednostką (np. '67%')")
    source_context: str | None = Field(None, description="Cytat ze źródła (20-50 słów)")
    confidence_level: str | None = Field(None, description="Pewność danych: high, medium, low")
    doc_id: str | None = Field(None, description="UUID dokumentu źródłowego")
    chunk_index: int | None = Field(None, description="Indeks fragmentu w dokumencie")
    document_title: str | None = Field(None, description="Tytuł dokumentu")
    document_country: str | None = Field(None, description="Kraj dokumentu")
    document_year: str | None = Field(None, description="Rok dokumentu")
    processed_at: str | None = Field(None, description="Timestamp przetwarzania")


class RelationshipProperties(BaseModel):
    """Metadane relacji w grafie wiedzy"""
    confidence: str | None = Field(None, description="Pewność relacji (0.0-1.0 jako string)")
    evidence: str | None = Field(None, description="Dowód/uzasadnienie relacji")
    strength: str | None = Field(None, description="Siła relacji: strong, moderate, weak")
    doc_id: str | None = Field(None, description="UUID dokumentu źródłowego")
    chunk_index: int | None = Field(None, description="Indeks fragmentu w dokumencie")


class GraphNode(BaseModel):
    """Node w grafie wiedzy"""
    id: str = Field(..., description="Unikalny identyfikator node")
    name: str = Field(..., description="Nazwa wyświetlana")
    type: str = Field(..., description="Typ: persona, concept, emotion")
    group: int = Field(..., description="Grupa dla kolorowania (1=persona, 2=concept, 3=emotion)")
    size: int = Field(..., description="Rozmiar node (proporcjonalny do ważności)")
    sentiment: float | None = Field(None, description="Sentiment score (-1.0 do 1.0)")
    metadata: JSONObject | None = Field(None, description="Dodatkowe dane")
    # properties: Optional[NodeProperties] = Field(None, description="Bogate metadane węzła z GraphRAG")
    # Note: Field 'properties' commented out - currently unused, can be re-enabled for GraphRAG


class GraphLink(BaseModel):
    """Połączenie między nodes w grafie"""
    source: str = Field(..., description="ID źródłowego node")
    target: str = Field(..., description="ID docelowego node")
    type: str = Field(..., description="Typ relacji: mentions, agrees, disagrees, feels")
    strength: float = Field(..., description="Siła połączenia (0.0-1.0)")
    sentiment: float | None = Field(None, description="Sentiment (dla MENTIONS)")
    # properties: Optional[RelationshipProperties] = Field(None, description="Metadane relacji z GraphRAG")
    # Note: Field 'properties' commented out - currently unused, can be re-enabled for GraphRAG


class GraphDataResponse(BaseModel):
    """Pełne dane grafu dla wizualizacji"""
    nodes: list[GraphNode] = Field(..., description="Lista wszystkich nodes")
    links: list[GraphLink] = Field(..., description="Lista wszystkich connections")


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
    personas: list[InfluentialPersona]


class KeyConcept(BaseModel):
    """Kluczowy koncept z dyskusji"""
    name: str
    frequency: int = Field(..., description="Liczba wzmianek")
    sentiment: float = Field(..., description="Średni sentiment")
    personas: list[str] = Field(..., description="Lista person wspominających")


class KeyConceptsResponse(BaseModel):
    """Lista kluczowych konceptów"""
    concepts: list[KeyConcept]


class GraphQueryInsight(BaseModel):
    """Pojedynczy insight zwrócony przez zapytanie"""
    title: str
    detail: str
    metadata: JSONObject = Field(default_factory=dict)


class GraphQueryRequest(BaseModel):
    """Zapytanie natural language do analizy grafu"""
    question: str = Field(..., min_length=1, max_length=500, description="Pytanie użytkownika")


class GraphQueryResponse(BaseModel):
    """Ustrukturyzowana odpowiedź na zapytanie"""
    answer: str
    insights: list[GraphQueryInsight] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
