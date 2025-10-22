"""Testy jednostkowe i integracyjne dla FocusGroupServiceLangChain."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.focus_groups import FocusGroupServiceLangChain


class DummyLLM:
    """Mock LLM do testów bez wywoływania prawdziwego API."""

    async def ainvoke(self, messages):
        """Symuluje wywołanie LLM zwracając predefiniowaną odpowiedź."""
        return SimpleNamespace(content="This is a great product idea with innovative features.")


class DummyFocusGroup:
    """Mock modelu FocusGroup."""

    def __init__(self):
        self.id = str(uuid4())
        self.name = "Test Focus Group"
        self.description = "Testing product feedback"
        self.questions = ["What do you think?", "Would you buy this?"]
        self.project_id = str(uuid4())
        self.status = "pending"
        self.started_at = None
        self.completed_at = None


class DummyPersona:
    """Mock modelu Persona."""

    def __init__(self, name="John Doe"):
        self.id = str(uuid4())
        self.name = name
        self.full_name = name  # Dodane dla zgodności z kodem produkcyjnym
        self.age = 30
        self.gender = "male"
        self.location = "Warsaw"
        self.education_level = "Master"
        self.income_bracket = "50k-70k"
        self.occupation = "Software Engineer"
        self.background_story = "A tech enthusiast who loves innovation."
        self.values = ["Innovation", "Quality"]
        self.interests = []  # Dodane dla zgodności z kodem produkcyjnym
        self.openness = 0.8
        self.conscientiousness = 0.7
        self.extraversion = 0.6
        self.agreeableness = 0.7
        self.neuroticism = 0.4


class DummyMemoryService:
    """Mock MemoryServiceLangChain."""

    async def record_event(self, *args, **kwargs):
        """Symuluje zapisywanie eventu do pamięci."""
        pass

    async def get_relevant_context(self, *args, **kwargs):
        """Symuluje pobieranie kontekstu z pamięci."""
        return []


@pytest.fixture
def service():
    """Tworzy instancję serwisu bez inicjalizacji prawdziwego LLM."""
    svc = FocusGroupServiceLangChain.__new__(FocusGroupServiceLangChain)
    svc.llm = DummyLLM()
    svc.memory_service = DummyMemoryService()
    return svc


@pytest.fixture
def mock_db():
    """Tworzy mock sesji bazodanowej."""
    db = AsyncMock()
    return db


# USUNIĘTO: 10 testów testujących nieistniejące prywatne metody
# Te testy były "sztuczne" - testowały API które nie istnieje w kodzie produkcyjnym
# Zamiast tego należy testować publiczne API (run_focus_group, _get_persona_response, etc.)


@pytest.mark.asyncio
async def test_context_retrieval_for_multi_question(service, mock_db):
    """Test pobierania kontekstu dla kolejnych pytań."""
    persona = DummyPersona("Alice")
    focus_group_id = str(uuid4())

    # Mock memory service zwracający kontekst
    service.memory_service.get_relevant_context = AsyncMock(return_value=[
        {
            "event_type": "response_given",
            "event_data": {
                "question": "Previous question?",
                "response": "Yes, I like it."
            },
            "timestamp": "2024-01-01T00:00:00"
        }
    ])

    context = await service.memory_service.get_relevant_context(
        persona_id=persona.id,
        query="Current question?",
        limit=5
    )

    assert len(context) > 0
    assert context[0]["event_type"] == "response_given"


# USUNIĘTO: test_empty_personas_raises_error - testował nieistniejącą metodę _load_focus_group_personas
# USUNIĘTO: test_prompt_includes_personality_traits - testował nieistniejącą metodę _create_persona_prompt


# ============================================================================
# NOWE TESTY ZACHOWANIA - Testujące Publiczne API i Faktyczną Funkcjonalność
# ============================================================================

@pytest.mark.asyncio
async def test_load_personas_from_ids(service, mock_db):
    """Test ładowania person z listy UUID - testuje _load_personas (ISTNIEJĄCĄ metodę)."""
    from uuid import uuid4
    persona_ids = [uuid4(), uuid4(), uuid4()]
    personas = [DummyPersona("Alice"), DummyPersona("Bob"), DummyPersona("Charlie")]

    # Mock wyniku query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = personas
    mock_db.execute.return_value = mock_result

    loaded = await service._load_personas(mock_db, persona_ids)

    assert len(loaded) == 3
    # Sprawdź że execute został wywołany
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_concurrent_responses_handles_exceptions(service, mock_db):
    """Test czy _get_concurrent_responses obsługuje wyjątki gracefully."""
    personas = [DummyPersona("Alice"), DummyPersona("Bob")]

    # Mock _get_persona_response aby rzucał wyjątek dla drugiej persony
    original_get_response = service._get_persona_response

    async def mock_get_response(persona, question, focus_group_id):
        if persona.name == "Bob":
            raise Exception("Network error")
        return {
            "persona_id": str(persona.id),
            "response": "Test response",
            "context_used": 0
        }

    service._get_persona_response = mock_get_response

    responses = await service._get_concurrent_responses(
        personas=personas,
        question="Test?",
        focus_group_id=str(uuid4())
    )

    # Powinny być 2 odpowiedzi, jedna normalna, jedna z errorem
    assert len(responses) == 2

    # Znajdź odpowiedź Boba (error)
    bob_response = next(r for r in responses if "error" in r or "Error" in r.get("response", ""))
    assert bob_response is not None

    service._get_persona_response = original_get_response


@pytest.mark.asyncio
async def test_create_response_prompt_includes_demographics(service):
    """Test czy _create_response_prompt (ISTNIEJĄCA metoda) zawiera dane demograficzne."""
    persona = DummyPersona("Alice")
    persona.age = 28
    persona.gender = "female"
    persona.occupation = "Designer"
    persona.location = "Warsaw"

    prompt = service._create_response_prompt(
        persona=persona,
        question="What do you think about the product?",
        context=[]
    )

    # Sprawdź czy prompt zawiera kluczowe dane persony
    assert "Alice" in prompt or persona.name in prompt
    assert "28" in prompt or str(persona.age) in prompt
    assert "Designer" in prompt or persona.occupation in prompt
    assert "What do you think about the product?" in prompt


def test_fallback_response_for_empty_llm(service):
    """Test czy _fallback_response generuje sensowną odpowiedź."""
    persona = DummyPersona("Alice")
    persona.occupation = "Designer"
    persona.full_name = "Alice Johnson"

    fallback = service._fallback_response(persona, "What's your opinion on the new feature?")

    # Fallback powinien zawierać nazwę i ocupation
    assert "Alice" in fallback
    assert "Designer" in fallback or persona.occupation.lower() in fallback.lower()
    assert len(fallback) > 20  # Sensowna długość


def test_pizza_fallback_response_personalized(service):
    """Test czy _pizza_fallback_response generuje spersonalizowaną odpowiedź."""
    persona = DummyPersona("Alice")
    persona.full_name = "Alice Johnson"
    persona.occupation = "Fitness Coach"
    persona.values = ["Health", "Wellness"]
    persona.interests = ["Yoga", "Running"]
    persona.location = "Warsaw"

    response = service._pizza_fallback_response(persona)

    # Powinna wybrać zdrową pizzę bazując na values
    assert "Alice" in response
    # "pizza" może być odmieniona (pizzę, pizzy, etc.) więc sprawdzamy "pizz"
    assert "pizz" in response.lower()
    assert len(response) > 50  # Szczegółowa odpowiedź
    # Powinno wspomnieć o zdrowiu bazując na values
    assert any(word in response.lower() for word in ["lekką", "lekka", "cienkim", "rukolą", "rukola", "warzywami", "zdrowych"])


@pytest.mark.asyncio
async def test_invoke_llm_handles_empty_response(service):
    """Test czy _invoke_llm prawidłowo obsługuje puste odpowiedzi."""

    # Mock LLM zwracający pusty content
    class EmptyLLM:
        async def ainvoke(self, messages):
            return SimpleNamespace(content="")

    service.llm = EmptyLLM()

    result = await service._invoke_llm("Test prompt")

    # Powinien zwrócić pusty string, nie None
    assert result == ""
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_invoke_llm_handles_list_content(service):
    """Test czy _invoke_llm scala fragmenty gdy content jest listą."""

    class ListLLM:
        async def ainvoke(self, messages):
            return SimpleNamespace(content=[
                {"text": "Hello "},
                {"text": "world"},
                "!"
            ])

    service.llm = ListLLM()

    result = await service._invoke_llm("Test")

    # Powinien scalić fragmenty
    assert "Hello" in result
    assert "world" in result
    assert len(result) > 0
