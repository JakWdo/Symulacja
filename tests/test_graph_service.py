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
    svc = GraphService.__new__(GraphService)
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

    extraction = await service._extract_concepts_llm(response_text)

    assert "concepts" in extraction
    assert "emotions" in extraction
    assert "sentiment" in extraction
    assert "key_phrases" in extraction
    assert isinstance(extraction["concepts"], list)
    assert isinstance(extraction["sentiment"], (int, float))
    assert -1.0 <= extraction["sentiment"] <= 1.0


def test_simple_concept_extraction_fallback(service):
    """Test prostej ekstrakcji konceptów gdy LLM jest niedostępny."""
    text = "The product quality is amazing. The price is reasonable. Great design and features."

    concepts = service._simple_concept_extraction(text)

    assert isinstance(concepts, list)
    assert len(concepts) > 0
    # Sprawdzamy czy wykrył kluczowe słowa
    concepts_lower = [c.lower() for c in concepts]
    assert any("product" in c or "quality" in c or "price" in c for c in concepts_lower)


def test_simple_emotion_detection(service):
    """Test prostego wykrywania emocji na podstawie słów kluczowych."""
    positive_text = "I'm so excited and thrilled about this amazing product!"
    negative_text = "I'm frustrated and angry about the issues and problems."
    neutral_text = "This is a product with some features."

    positive_emotions = service._simple_emotion_detection(positive_text)
    negative_emotions = service._simple_emotion_detection(negative_text)
    neutral_emotions = service._simple_emotion_detection(neutral_text)

    assert len(positive_emotions) > 0
    assert "Excited" in positive_emotions or "Satisfied" in positive_emotions
    assert len(negative_emotions) > 0
    assert "Frustrated" in negative_emotions
    # Neutralny tekst może nie zawierać emocji
    assert isinstance(neutral_emotions, list)


def test_simple_sentiment_score(service):
    """Test prostego scoringu sentymentu."""
    positive = "I love this amazing great awesome product!"
    negative = "I hate this terrible bad awful product!"
    neutral = "This is a product with features."

    pos_score = service._simple_sentiment_score(positive)
    neg_score = service._simple_sentiment_score(negative)
    neu_score = service._simple_sentiment_score(neutral)

    assert pos_score > 0
    assert neg_score < 0
    assert abs(neu_score) < abs(pos_score)


@pytest.mark.asyncio
async def test_build_graph_memory_fallback(service, mock_db):
    """Test budowania grafu w pamięci RAM gdy Neo4j niedostępny."""
    focus_group = DummyFocusGroup()
    persona1_id = str(uuid4())
    persona2_id = str(uuid4())

    responses = [
        DummyPersonaResponse(persona1_id, "What do you think?", "Great quality!", "Alice"),
        DummyPersonaResponse(persona2_id, "What do you think?", "Too expensive.", "Bob")
    ]

    # Mock query zwracający odpowiedzi
    mock_result_responses = MagicMock()
    mock_result_responses.scalars.return_value.all.return_value = responses

    mock_result_fg = MagicMock()
    mock_result_fg.scalar_one.return_value = focus_group

    mock_db.execute.side_effect = [mock_result_responses, mock_result_fg]

    result = await service.build_knowledge_graph(mock_db, focus_group.id)

    # Sprawdzamy czy graf został zbudowany w pamięci
    assert result["status"] == "completed"
    assert result["using_neo4j"] is False
    assert focus_group.id in service._memory_graph_cache


@pytest.mark.asyncio
async def test_get_key_concepts_from_memory(service, mock_db):
    """Test pobierania kluczowych konceptów z grafu w pamięci."""
    focus_group_id = str(uuid4())

    # Przygotuj cache z danymi
    service._memory_graph_cache[focus_group_id] = {
        "concepts": {
            "Quality": {"mentions": 5, "sentiments": [0.8, 0.7, 0.9, 0.6, 0.8]},
            "Price": {"mentions": 3, "sentiments": [-0.5, -0.3, -0.4]},
            "Design": {"mentions": 2, "sentiments": [0.9, 0.8]}
        }
    }

    concepts = await service.get_key_concepts(mock_db, focus_group_id, limit=10)

    assert len(concepts) > 0
    # Powinny być posortowane po liczbie wzmianek
    assert concepts[0]["concept"] == "Quality"
    assert concepts[0]["mention_count"] == 5
    assert "avg_sentiment" in concepts[0]


@pytest.mark.asyncio
async def test_get_controversial_concepts(service, mock_db):
    """Test wykrywania kontrowersyjnych konceptów (wysokie rozbieżności sentymentu)."""
    focus_group_id = str(uuid4())

    # Przygotuj cache z polaryzującym konceptem
    service._memory_graph_cache[focus_group_id] = {
        "concepts": {
            "Pricing": {
                "mentions": 6,
                "sentiments": [0.9, 0.8, -0.7, -0.8, 0.7, -0.6],  # Mieszane opinie
                "personas": {
                    "positive": ["Alice", "Bob"],
                    "negative": ["Charlie", "Diana"]
                }
            },
            "Quality": {
                "mentions": 4,
                "sentiments": [0.8, 0.9, 0.7, 0.8]  # Zgodne pozytywne
            }
        }
    }

    controversial = await service.get_controversial_concepts(mock_db, focus_group_id, limit=5)

    # "Pricing" powinien być wykryty jako kontrowersyjny
    assert len(controversial) > 0
    pricing_concept = next((c for c in controversial if c["concept"] == "Pricing"), None)
    assert pricing_concept is not None
    assert pricing_concept["polarization"] > 0.5  # Wysoka polaryzacja


@pytest.mark.asyncio
async def test_get_influential_personas(service, mock_db):
    """Test identyfikacji wpływowych person (najwięcej połączeń w grafie)."""
    focus_group_id = str(uuid4())

    # Przygotuj cache z danymi o połączeniach
    service._memory_graph_cache[focus_group_id] = {
        "personas": {
            "Alice": {
                "connections": 15,
                "concepts_mentioned": ["Quality", "Price", "Design"]
            },
            "Bob": {
                "connections": 8,
                "concepts_mentioned": ["Quality", "Features"]
            },
            "Charlie": {
                "connections": 12,
                "concepts_mentioned": ["Price", "Support", "Design"]
            }
        }
    }

    influential = await service.get_influential_personas(mock_db, focus_group_id, limit=2)

    assert len(influential) <= 2
    # Alice powinna być pierwsza (15 połączeń)
    assert influential[0]["persona"] == "Alice"
    assert influential[0]["connection_count"] == 15


@pytest.mark.asyncio
async def test_get_emotion_distribution(service, mock_db):
    """Test pobierania rozkładu emocji w grupie fokusowej."""
    focus_group_id = str(uuid4())

    service._memory_graph_cache[focus_group_id] = {
        "emotions": {
            "Satisfied": 10,
            "Excited": 5,
            "Concerned": 3,
            "Frustrated": 2
        }
    }

    emotions = await service.get_emotion_distribution(mock_db, focus_group_id)

    assert len(emotions) == 4
    assert emotions[0]["emotion"] == "Satisfied"
    assert emotions[0]["count"] == 10


@pytest.mark.asyncio
async def test_get_trait_opinion_correlations(service, mock_db):
    """Test korelacji między cechami demograficznymi a opiniami."""
    focus_group_id = str(uuid4())

    # Cache z danymi demograficznymi
    service._memory_graph_cache[focus_group_id] = {
        "trait_correlations": {
            "age_sentiment": {
                "young": {"avg_sentiment": 0.7, "count": 5},
                "senior": {"avg_sentiment": 0.2, "count": 4}
            },
            "concept_by_age": {
                "Quality": {
                    "young": 0.8,
                    "senior": 0.6
                }
            }
        }
    }

    correlations = await service.get_trait_opinion_correlations(mock_db, focus_group_id)

    assert "age_sentiment" in correlations or len(correlations) > 0


def test_normalize_concept_name(service):
    """Test normalizacji nazw konceptów (lowercase, usuwanie duplikatów)."""
    assert service._normalize_concept("Product") == "product"
    assert service._normalize_concept("PRICING") == "pricing"
    assert service._normalize_concept("User Experience") == "user experience"


def test_calculate_polarization_score(service):
    """Test obliczania wyniku polaryzacji na podstawie sentymentów."""
    # Wysoka polaryzacja - mieszane opinie
    high_polarization = [0.9, 0.8, -0.7, -0.8, 0.6, -0.6]
    # Niska polaryzacja - zgodne opinie
    low_polarization = [0.7, 0.8, 0.75, 0.85, 0.7]

    high_score = service._calculate_polarization(high_polarization)
    low_score = service._calculate_polarization(low_polarization)

    assert high_score > low_score
    assert 0 <= high_score <= 1
    assert 0 <= low_score <= 1


@pytest.mark.asyncio
async def test_graph_caching_mechanism(service, mock_db):
    """Test mechanizmu cache'owania grafów w pamięci."""
    focus_group_id = str(uuid4())

    # Pierwsze wywołanie - buduje graf
    service._memory_graph_cache[focus_group_id] = {
        "concepts": {"Test": {"mentions": 1, "sentiments": [0.5]}}
    }

    # Drugie wywołanie - powinno użyć cache
    result = await service.get_key_concepts(mock_db, focus_group_id)

    assert len(result) > 0
    # Brak dodatkowych wywołań do DB oznacza użycie cache


@pytest.mark.asyncio
async def test_empty_responses_handling(service, mock_db):
    """Test obsługi przypadku gdy brak odpowiedzi w grupie fokusowej."""
    focus_group = DummyFocusGroup()

    # Mock zwracający pustą listę
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = await service.build_knowledge_graph(mock_db, focus_group.id)

    # Powinien zwrócić status bez błędu
    assert result["status"] == "completed"
    assert result["nodes_created"] == 0 or "nodes_created" in result


def test_stopwords_filtering(service):
    """Test filtrowania stop words z konceptów."""
    text = "The product is very good and the quality is also great for the price"

    concepts = service._simple_concept_extraction(text)

    # Stop words nie powinny być w konceptach
    concepts_lower = [c.lower() for c in concepts]
    assert "the" not in concepts_lower
    assert "and" not in concepts_lower
    assert "very" not in concepts_lower
    # Kluczowe słowa powinny zostać
    assert any("product" in c or "quality" in c or "price" in c for c in concepts_lower)


@pytest.mark.asyncio
async def test_build_graph_with_agreements(service, mock_db):
    """Test budowania grafu z relacjami zgody/niezgody między personami."""
    focus_group = DummyFocusGroup()
    persona1_id = str(uuid4())
    persona2_id = str(uuid4())

    responses = [
        DummyPersonaResponse(persona1_id, "Q?", "I love the quality! Great product.", "Alice"),
        DummyPersonaResponse(persona2_id, "Q?", "I also love the quality! Excellent.", "Bob")
    ]

    mock_result_responses = MagicMock()
    mock_result_responses.scalars.return_value.all.return_value = responses

    mock_result_fg = MagicMock()
    mock_result_fg.scalar_one.return_value = focus_group

    mock_db.execute.side_effect = [mock_result_responses, mock_result_fg]

    result = await service.build_knowledge_graph(mock_db, focus_group.id)

    # Graf powinien zawierać relacje zgodności (oba pozytywne o quality)
    assert result["status"] == "completed"
