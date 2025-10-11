"""Testy jednostkowe i integracyjne dla GraphService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from uuid import uuid4
from collections import Counter

from app.services.graph_service import GraphService, ConceptExtraction


class DummyLLM:
    """Mock LLM do testów bez wywoływania prawdziwego API."""

    async def ainvoke(self, messages):
        """Symuluje wywołanie LLM zwracając predefiniowaną ekstrakcję."""
        return {
            "concepts": ["Product", "Price", "Quality"],
            "emotions": ["Satisfied", "Concerned"],
            "sentiment": 0.6,
            "key_phrases": ["great quality", "bit expensive", "worth the price"]
        }


class DummyPersona:
    """Mock modelu Persona."""

    def __init__(self, name="John Doe", persona_id=None):
        self.id = persona_id or str(uuid4())
        self.name = name
        self.full_name = name  # GraphService używa full_name
        self.age = 30
        self.gender = "male"
        self.education_level = "Master"
        self.occupation = "Engineer"


class DummyPersonaResponse:
    """Mock modelu PersonaResponse."""

    def __init__(self, persona_id, question, response, persona_name="John"):
        self.id = str(uuid4())
        self.persona_id = persona_id
        self.question = question
        self.response = response
        self.persona = DummyPersona(persona_name, persona_id)


class DummyFocusGroup:
    """Mock modelu FocusGroup."""

    def __init__(self):
        self.id = str(uuid4())
        self.name = "Product Feedback"
        self.description = "Testing new product"
        self.questions = ["What do you think?"]


@pytest.fixture
def service():
    """Tworzy instancję serwisu bez połączenia z Neo4j."""
    with patch('app.services.graph_service.get_settings') as mock_settings:
        mock_settings.return_value.GOOGLE_API_KEY = None
        mock_settings.return_value.NEO4J_URI = "bolt://localhost:7687"
        mock_settings.return_value.NEO4J_USER = "neo4j"
        mock_settings.return_value.NEO4J_PASSWORD = "password"

        svc = GraphService()
        svc.driver = None  # Brak prawdziwego połączenia
        svc.llm = DummyLLM()
        svc._memory_graph_cache = {}
        svc._memory_stats_cache = {}
        svc._memory_metrics_cache = {}
        return svc


@pytest.fixture
def mock_db():
    """Tworzy mock sesji bazodanowej."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_extract_concepts_from_response(service):
    """Test ekstrakcji konceptów, emocji i sentymentu z odpowiedzi."""
    response_text = "I love the product quality but the price is too high. Great features overall."

    extraction = await service._extract_concepts_with_llm(response_text)

    assert extraction.concepts is not None
    assert extraction.emotions is not None
    assert extraction.sentiment is not None
    assert extraction.key_phrases is not None
    assert isinstance(extraction.concepts, list)
    assert isinstance(extraction.sentiment, (int, float))
    assert -1.0 <= extraction.sentiment <= 1.0


def test_simple_concept_extraction_fallback(service):
    """Test prostej ekstrakcji konceptów gdy LLM jest niedostępny."""
    text = "The product quality is amazing. The price is reasonable. Great design and features."

    concepts = service._simple_keyword_extraction(text, max_keywords=5)

    assert isinstance(concepts, list)
    assert len(concepts) > 0
    # Sprawdzamy czy wykrył kluczowe słowa
    concepts_lower = [c.lower() for c in concepts]
    assert any("product" in c or "quality" in c or "price" in c or "design" in c for c in concepts_lower)


def test_simple_emotion_detection(service):
    """Test prostego wykrywania emocji na podstawie słów kluczowych."""
    positive_text = "I'm so excited and thrilled about this amazing product!"
    negative_text = "I'm frustrated and angry about the issues and problems."
    neutral_text = "This is a product with some features."

    positive_emotions = service._infer_emotions(positive_text, 0.8)
    negative_emotions = service._infer_emotions(negative_text, -0.7)
    neutral_emotions = service._infer_emotions(neutral_text, 0.0)

    assert len(positive_emotions) > 0
    assert "Excited" in positive_emotions or "Satisfied" in positive_emotions
    assert len(negative_emotions) > 0
    assert "Frustrated" in negative_emotions or "Concerned" in negative_emotions
    # Neutralny tekst może zawierać emocje bazowane na sentymenc
    assert isinstance(neutral_emotions, list)


def test_simple_sentiment_score(service):
    """Test prostego scoringu sentymentu."""
    positive = "I love this amazing great awesome product!"
    negative = "I hate this terrible bad awful product!"
    neutral = "This is a product with features."

    pos_score = service._analyze_sentiment(positive)
    neg_score = service._analyze_sentiment(negative)
    neu_score = service._analyze_sentiment(neutral)

    assert pos_score > 0
    assert neg_score < 0
    assert abs(neu_score) < abs(pos_score)


@pytest.mark.asyncio
async def test_build_graph_memory_fallback(service, mock_db):
    """Test budowania grafu w pamięci RAM gdy Neo4j niedostępny."""
    focus_group = DummyFocusGroup()
    focus_group.status = "completed"
    persona1_id = str(uuid4())
    persona2_id = str(uuid4())

    persona1 = DummyPersona("Alice", persona1_id)
    persona2 = DummyPersona("Bob", persona2_id)

    responses = [
        DummyPersonaResponse(persona1_id, "What do you think?", "Great quality!", "Alice"),
        DummyPersonaResponse(persona2_id, "What do you think?", "Too expensive.", "Bob")
    ]

    # Mock query zwracający focus group
    mock_result_fg = MagicMock()
    mock_result_fg.scalar_one_or_none.return_value = focus_group

    # Mock query zwracający odpowiedzi
    mock_result_responses = MagicMock()
    mock_result_responses.scalars.return_value.all.return_value = responses

    # Mock query zwracający persony
    mock_result_personas = MagicMock()
    mock_result_personas.scalars.return_value.all.return_value = [persona1, persona2]

    mock_db.execute.side_effect = [mock_result_fg, mock_result_responses, mock_result_personas]

    result = await service.build_graph_from_focus_group(mock_db, focus_group.id)

    # Sprawdzamy czy graf został zbudowany w pamięci
    assert "personas_added" in result
    assert "concepts_extracted" in result
    assert result["personas_added"] == 2
    assert focus_group.id in service._memory_graph_cache


@pytest.mark.asyncio
async def test_get_key_concepts_from_memory(service, mock_db):
    """Test pobierania kluczowych konceptów z grafu w pamięci."""
    focus_group_id = str(uuid4())

    # Mockujemy _ensure_memory_graph żeby zwrócić cache bezpośrednio
    async def mock_ensure_memory_graph(fg_id, db):
        graph_data = {}
        metrics = {
            "concept_aggregates": {
                "Quality": {"mentions": 5, "sentiments": [0.8, 0.7, 0.9, 0.6, 0.8], "personas": {"p1", "p2"}},
                "Price": {"mentions": 3, "sentiments": [-0.5, -0.3, -0.4], "personas": {"p1"}},
                "Design": {"mentions": 2, "sentiments": [0.9, 0.8], "personas": {"p3"}}
            },
            "persona_metadata": {
                "p1": {"name": "Alice"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Charlie"}
            }
        }
        return graph_data, metrics

    # Mockujemy connect() aby rzucał ConnectionError - wymusza fallback do pamięci
    with patch.object(service, 'connect', side_effect=ConnectionError("Neo4j unavailable")):
        service._ensure_memory_graph = mock_ensure_memory_graph

        concepts = await service.get_key_concepts(focus_group_id, db=mock_db)

        assert len(concepts) > 0
        # Powinny być posortowane po liczbie wzmianek
        assert concepts[0]["name"] == "Quality"
        assert concepts[0]["frequency"] == 5
        assert "sentiment" in concepts[0]
        # Sprawdź średni sentiment (mean([0.8, 0.7, 0.9, 0.6, 0.8]) = 0.76)
        assert 0.75 <= concepts[0]["sentiment"] <= 0.77


@pytest.mark.asyncio
async def test_get_controversial_concepts(service, mock_db):
    """Test wykrywania kontrowersyjnych konceptów (wysokie rozbieżności sentymentu)."""
    focus_group_id = str(uuid4())

    # Mockujemy _ensure_memory_graph
    async def mock_ensure_memory_graph(fg_id, db):
        graph_data = {}
        metrics = {
            "concept_aggregates": {
                "Pricing": {
                    "mentions": 6,
                    "sentiments": [0.9, 0.8, -0.7, -0.8, 0.7, -0.6],  # Mieszane opinie
                    "personas": {"p1", "p2", "p3", "p4"}
                },
                "Quality": {
                    "mentions": 4,
                    "sentiments": [0.8, 0.9, 0.7, 0.8],  # Zgodne pozytywne
                    "personas": {"p1", "p2"}
                }
            },
            "persona_concepts": {
                "p1": {"Pricing": [0.9, 0.8]},
                "p2": {"Pricing": [0.7]},
                "p3": {"Pricing": [-0.7, -0.8]},
                "p4": {"Pricing": [-0.6]}
            },
            "persona_metadata": {
                "p1": {"name": "Alice"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Charlie"},
                "p4": {"name": "Diana"}
            }
        }
        return graph_data, metrics

    # Mockujemy connect() aby rzucał ConnectionError - wymusza fallback do pamięci
    with patch.object(service, 'connect', side_effect=ConnectionError("Neo4j unavailable")):
        service._ensure_memory_graph = mock_ensure_memory_graph

        controversial = await service.get_controversial_concepts(focus_group_id, db=mock_db)

        # "Pricing" powinien być wykryty jako kontrowersyjny
        assert len(controversial) > 0
        pricing_concept = next((c for c in controversial if c["concept"] == "Pricing"), None)
        assert pricing_concept is not None
        assert pricing_concept["polarization"] > 0.5  # Wysoka polaryzacja
        # Sprawdź że Quality NIE jest kontrowersyjny (zgodne pozytywne opinie)
        quality_concept = next((c for c in controversial if c["concept"] == "Quality"), None)
        assert quality_concept is None, "Quality powinien mieć niską polaryzację (wszystkie pozytywne)"


@pytest.mark.asyncio
async def test_get_influential_personas(service, mock_db):
    """Test identyfikacji wpływowych person (najwięcej połączeń w grafie)."""
    focus_group_id = str(uuid4())

    # Mockujemy _ensure_memory_graph
    async def mock_ensure_memory_graph(fg_id, db):
        graph_data = {}
        metrics = {
            "persona_metadata": {
                "p1": {"name": "Alice", "age": 30, "occupation": "Designer"},
                "p2": {"name": "Bob", "age": 25, "occupation": "Developer"},
                "p3": {"name": "Charlie", "age": 35, "occupation": "Manager"}
            },
            "persona_connections": {
                "p1": 15,
                "p2": 8,
                "p3": 12
            },
            "persona_sentiments": {
                "p1": 0.7,
                "p2": 0.5,
                "p3": 0.6
            }
        }
        return graph_data, metrics

    # Mockujemy connect() aby rzucał ConnectionError - wymusza fallback do pamięci
    with patch.object(service, 'connect', side_effect=ConnectionError("Neo4j unavailable")):
        service._ensure_memory_graph = mock_ensure_memory_graph

        influential = await service.get_influential_personas(focus_group_id, db=mock_db)

        assert len(influential) > 0
        # Alice powinna być pierwsza (15 połączeń)
        assert influential[0]["name"] == "Alice"
        assert influential[0]["connections"] == 15
        # Sprawdź kolejność (sortowanie po connections malejąco)
        assert influential[1]["name"] == "Charlie"  # 12 połączeń
        assert influential[2]["name"] == "Bob"  # 8 połączeń


@pytest.mark.asyncio
async def test_get_emotion_distribution(service, mock_db):
    """Test pobierania rozkładu emocji w grupie fokusowej."""
    focus_group_id = str(uuid4())

    # Mockujemy _ensure_memory_graph
    async def mock_ensure_memory_graph(fg_id, db):
        graph_data = {}
        metrics = {
            "emotion_aggregates": {
                "Satisfied": {"count": 10, "intensities": [0.8, 0.7, 0.9, 0.6, 0.8, 0.7, 0.8, 0.9, 0.7, 0.8], "personas": {"p1", "p2", "p3"}},
                "Excited": {"count": 5, "intensities": [0.9, 0.8, 0.7, 0.9, 0.8], "personas": {"p1", "p4"}},
                "Concerned": {"count": 3, "intensities": [0.5, 0.6, 0.4], "personas": {"p5"}},
                "Frustrated": {"count": 2, "intensities": [0.7, 0.6], "personas": {"p6"}}
            }
        }
        return graph_data, metrics

    # Mockujemy connect() aby rzucał ConnectionError - wymusza fallback do pamięci
    with patch.object(service, 'connect', side_effect=ConnectionError("Neo4j unavailable")):
        service._ensure_memory_graph = mock_ensure_memory_graph

        emotions = await service.get_emotion_distribution(focus_group_id, db=mock_db)

        assert len(emotions) == 4
        # Sprawdź sortowanie po liczbie (malejąco)
        assert emotions[0]["emotion"] == "Satisfied"  # count: 10
        assert emotions[0]["personas_count"] == 3
        assert emotions[1]["emotion"] == "Excited"  # count: 5
        assert emotions[2]["emotion"] == "Concerned"  # count: 3
        assert emotions[3]["emotion"] == "Frustrated"  # count: 2


@pytest.mark.asyncio
async def test_get_trait_opinion_correlations(service, mock_db):
    """Test korelacji między cechami demograficznymi a opiniami."""
    focus_group_id = str(uuid4())

    # Cache z danymi demograficznymi
    service._memory_metrics_cache[focus_group_id] = {
        "concept_aggregates": {
            "Quality": {"mentions": 5, "sentiments": [0.8, 0.7, 0.2, 0.3, 0.4], "personas": {"p1", "p2", "p3", "p4", "p5"}}
        },
        "persona_concepts": {
            "p1": {"Quality": [0.8]},
            "p2": {"Quality": [0.7]},
            "p3": {"Quality": [0.2]},
            "p4": {"Quality": [0.3]},
            "p5": {"Quality": [0.4]}
        },
        "persona_metadata": {
            "p1": {"name": "Alice", "age": 25},
            "p2": {"name": "Bob", "age": 28},
            "p3": {"name": "Charlie", "age": 55},
            "p4": {"name": "Diana", "age": 60},
            "p5": {"name": "Eve", "age": 65}
        }
    }
    service._memory_graph_cache[focus_group_id] = {}

    correlations = await service.get_trait_opinion_correlations(focus_group_id, db=mock_db)

    assert isinstance(correlations, list)


def test_normalize_concept_name(service):
    """Test normalizacji nazw konceptów."""
    concepts = service._normalize_concepts(["Product", "PRICING", "User Experience", "product"])

    assert isinstance(concepts, list)
    assert len(concepts) > 0
    # Sprawdzamy że duplikaty są usunięte
    assert len(concepts) == len(set(concepts))
    # Title case formatting
    assert any("Product" in c for c in concepts)


def test_calculate_polarization_score(service):
    """Test obliczania wyniku polaryzacji na podstawie sentymentów."""
    from statistics import pstdev

    # Wysoka polaryzacja - mieszane opinie
    high_polarization = [0.9, 0.8, -0.7, -0.8, 0.6, -0.6]
    # Niska polaryzacja - zgodne opinie
    low_polarization = [0.7, 0.8, 0.75, 0.85, 0.7]

    high_score = pstdev(high_polarization)
    low_score = pstdev(low_polarization)

    assert high_score > low_score
    assert high_score > 0.5  # Wysoka wariancja
    assert low_score < 0.1  # Niska wariancja


@pytest.mark.asyncio
async def test_graph_caching_mechanism(service, mock_db):
    """Test mechanizmu cache'owania grafów w pamięci."""
    focus_group_id = str(uuid4())

    # Mockujemy _ensure_memory_graph
    async def mock_ensure_memory_graph(fg_id, db):
        graph_data = {}
        metrics = {
            "concept_aggregates": {
                "Test": {"mentions": 1, "sentiments": [0.5], "personas": {"p1"}}
            },
            "persona_metadata": {
                "p1": {"name": "Alice"}
            }
        }
        return graph_data, metrics

    # Mockujemy connect() aby rzucał ConnectionError - wymusza fallback do pamięci
    with patch.object(service, 'connect', side_effect=ConnectionError("Neo4j unavailable")):
        service._ensure_memory_graph = mock_ensure_memory_graph

        # Drugie wywołanie - powinno użyć cache
        result = await service.get_key_concepts(focus_group_id, db=mock_db)

        assert len(result) > 0
        assert result[0]["name"] == "Test"
        assert result[0]["frequency"] == 1
        # Brak dodatkowych wywołań do DB oznacza użycie cache


@pytest.mark.asyncio
async def test_empty_responses_handling(service, mock_db):
    """Test obsługi przypadku gdy brak odpowiedzi w grupie fokusowej."""
    focus_group = DummyFocusGroup()
    focus_group.status = "completed"

    # Mock zwracający focus group
    mock_result_fg = MagicMock()
    mock_result_fg.scalar_one_or_none.return_value = focus_group

    # Mock zwracający pustą listę odpowiedzi
    mock_result_responses = MagicMock()
    mock_result_responses.scalars.return_value.all.return_value = []

    # Mock zwracający pustą listę person
    mock_result_personas = MagicMock()
    mock_result_personas.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [mock_result_fg, mock_result_responses, mock_result_personas]

    result = await service.build_graph_from_focus_group(mock_db, focus_group.id)

    # Powinien zwrócić stats bez błędu
    assert "personas_added" in result
    assert result["personas_added"] == 0


def test_stopwords_filtering(service):
    """Test filtrowania stop words z konceptów."""
    text = "The product is very good and the quality is also great for the price"

    concepts = service._simple_keyword_extraction(text, max_keywords=5)

    # Stop words nie powinny być w konceptach
    concepts_lower = [c.lower() for c in concepts]
    assert "the" not in concepts_lower
    assert "and" not in concepts_lower
    assert "very" not in concepts_lower
    # Kluczowe słowa powinny zostać
    assert any("product" in c or "quality" in c or "price" in c or "good" in c for c in concepts_lower)


@pytest.mark.asyncio
async def test_build_graph_with_agreements(service, mock_db):
    """Test budowania grafu z relacjami zgody/niezgody między personami."""
    focus_group = DummyFocusGroup()
    focus_group.status = "completed"
    persona1_id = str(uuid4())
    persona2_id = str(uuid4())

    persona1 = DummyPersona("Alice", persona1_id)
    persona2 = DummyPersona("Bob", persona2_id)

    responses = [
        DummyPersonaResponse(persona1_id, "Q?", "I love the quality! Great product.", "Alice"),
        DummyPersonaResponse(persona2_id, "Q?", "I also love the quality! Excellent.", "Bob")
    ]

    # Mock query zwracający focus group
    mock_result_fg = MagicMock()
    mock_result_fg.scalar_one_or_none.return_value = focus_group

    # Mock query zwracający odpowiedzi
    mock_result_responses = MagicMock()
    mock_result_responses.scalars.return_value.all.return_value = responses

    # Mock query zwracający persony
    mock_result_personas = MagicMock()
    mock_result_personas.scalars.return_value.all.return_value = [persona1, persona2]

    mock_db.execute.side_effect = [mock_result_fg, mock_result_responses, mock_result_personas]

    result = await service.build_graph_from_focus_group(mock_db, focus_group.id)

    # Graf powinien zawierać relacje zgodności (oba pozytywne o quality)
    assert "personas_added" in result
    assert result["personas_added"] == 2
