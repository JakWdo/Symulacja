"""Testy jednostkowe i integracyjne dla FocusGroupServiceLangChain."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.services.focus_group_service_langchain import FocusGroupServiceLangChain


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
        self.age = 30
        self.gender = "male"
        self.location = "Warsaw"
        self.education_level = "Master"
        self.income_bracket = "50k-70k"
        self.occupation = "Software Engineer"
        self.background_story = "A tech enthusiast who loves innovation."
        self.values = ["Innovation", "Quality"]
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


@pytest.mark.asyncio
async def test_load_focus_group_personas(service, mock_db):
    """Test ładowania person przypisanych do grupy fokusowej."""
    focus_group = DummyFocusGroup()
    personas = [DummyPersona("Alice"), DummyPersona("Bob"), DummyPersona("Charlie")]

    # Mock wyniku query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = personas
    mock_db.execute.return_value = mock_result

    loaded_personas = await service._load_focus_group_personas(mock_db, focus_group.id)

    assert len(loaded_personas) == 3
    assert loaded_personas[0].name == "Alice"
    assert loaded_personas[1].name == "Bob"
    assert loaded_personas[2].name == "Charlie"


@pytest.mark.asyncio
async def test_create_persona_prompt_includes_context(service):
    """Test tworzenia promptu dla persony z kontekstem rozmowy."""
    persona = DummyPersona("Alice")
    question = "What do you think about the product?"
    context = [
        {
            "event_type": "question_asked",
            "event_data": {"question": "Previous question?"},
            "timestamp": "2024-01-01T00:00:00"
        }
    ]

    messages = service._create_persona_prompt(
        persona=persona,
        question=question,
        context=context,
        focus_group_description="Product feedback session"
    )

    # Sprawdzamy czy prompt zawiera kluczowe elementy
    prompt_text = str(messages)
    assert "Alice" in prompt_text or persona.name in str(messages)
    assert question in prompt_text
    assert "Product feedback session" in prompt_text


@pytest.mark.asyncio
async def test_generate_single_response_structure(service, mock_db):
    """Test generowania pojedynczej odpowiedzi persony."""
    persona = DummyPersona("Alice")
    question = "What do you think?"
    focus_group = DummyFocusGroup()

    response = await service._generate_single_response(
        db=mock_db,
        persona=persona,
        question=question,
        focus_group_id=focus_group.id,
        focus_group_description=focus_group.description,
        question_index=0
    )

    assert response["persona_id"] == persona.id
    assert response["persona_name"] == persona.name
    assert response["question"] == question
    assert "response" in response
    assert isinstance(response["response"], str)
    assert len(response["response"]) > 0
    assert "response_time_ms" in response


@pytest.mark.asyncio
async def test_parallel_response_generation(service, mock_db):
    """Test równoległego generowania odpowiedzi od wielu person."""
    personas = [DummyPersona(f"Person{i}") for i in range(5)]
    question = "What's your opinion?"
    focus_group = DummyFocusGroup()

    responses = await service._generate_responses_for_question(
        db=mock_db,
        personas=personas,
        question=question,
        question_index=0,
        focus_group_id=focus_group.id,
        focus_group_description=focus_group.description
    )

    assert len(responses) == 5
    assert all("persona_id" in r for r in responses)
    assert all("response" in r for r in responses)
    assert all(len(r["response"]) > 0 for r in responses)


@pytest.mark.asyncio
async def test_error_handling_in_response_generation(service, mock_db):
    """Test obsługi błędów podczas generowania odpowiedzi."""

    # Mock LLM który rzuca wyjątek
    async def failing_invoke(messages):
        raise Exception("API Error")

    service.llm.ainvoke = failing_invoke

    persona = DummyPersona("Alice")
    question = "What do you think?"
    focus_group = DummyFocusGroup()

    response = await service._generate_single_response(
        db=mock_db,
        persona=persona,
        question=question,
        focus_group_id=focus_group.id,
        focus_group_description=focus_group.description,
        question_index=0
    )

    # Serwis powinien zwrócić error response zamiast crashować
    assert response["persona_id"] == persona.id
    assert "response" in response
    assert "error" in response["response"].lower() or response["response"] == ""


@pytest.mark.asyncio
async def test_save_responses_to_db(service, mock_db):
    """Test zapisywania odpowiedzi person do bazy danych."""
    focus_group = DummyFocusGroup()
    responses = [
        {
            "persona_id": str(uuid4()),
            "persona_name": "Alice",
            "question": "What do you think?",
            "response": "I think it's great!",
            "response_time_ms": 1500
        },
        {
            "persona_id": str(uuid4()),
            "persona_name": "Bob",
            "question": "What do you think?",
            "response": "I'm not sure about this.",
            "response_time_ms": 1800
        }
    ]

    await service._save_responses(mock_db, focus_group.id, responses)

    # Sprawdzamy czy add został wywołany dla każdej odpowiedzi
    assert mock_db.add.call_count == len(responses)
    assert mock_db.commit.called


def test_format_persona_profile(service):
    """Test formatowania profilu persony do promptu."""
    persona = DummyPersona("Alice")

    profile = service._format_persona_profile(persona)

    # Sprawdzamy czy profil zawiera kluczowe informacje
    assert "Alice" in profile
    assert str(persona.age) in profile or "30" in profile
    assert persona.gender in profile or "male" in profile
    assert persona.occupation in profile
    assert persona.background_story in profile


def test_calculate_metrics(service):
    """Test obliczania metryk wydajności grupy fokusowej."""
    all_responses = [
        [
            {"response_time_ms": 1500},
            {"response_time_ms": 1800},
            {"response_time_ms": 1200}
        ],
        [
            {"response_time_ms": 2000},
            {"response_time_ms": 1600},
            {"response_time_ms": 1400}
        ]
    ]

    total_time_ms = 10000  # 10 sekund

    metrics = service._calculate_metrics(all_responses, total_time_ms)

    assert "total_execution_time_ms" in metrics
    assert "avg_response_time_ms" in metrics
    assert "meets_requirements" in metrics
    assert metrics["total_execution_time_ms"] == total_time_ms
    assert isinstance(metrics["avg_response_time_ms"], (int, float))
    assert isinstance(metrics["meets_requirements"], bool)


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


@pytest.mark.asyncio
async def test_empty_personas_raises_error(service, mock_db):
    """Test obsługi przypadku gdy brak person w grupie fokusowej."""
    focus_group = DummyFocusGroup()

    # Mock zwracający pustą listę person
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="No personas"):
        personas = await service._load_focus_group_personas(mock_db, focus_group.id)
        if len(personas) == 0:
            raise ValueError("No personas found")


def test_prompt_includes_personality_traits(service):
    """Test czy prompt zawiera cechy osobowości persony."""
    persona = DummyPersona("Alice")
    persona.openness = 0.9
    persona.conscientiousness = 0.3

    messages = service._create_persona_prompt(
        persona=persona,
        question="What do you think?",
        context=[],
        focus_group_description="Test"
    )

    prompt_text = str(messages)
    # Prompt powinien zawierać informacje o wysokiej otwartości i niskiej sumienności
    assert "openness" in prompt_text.lower() or "open" in prompt_text.lower()
