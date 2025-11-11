"""Testy jednostkowe dla SurveyResponseGenerator - zaktualizowane."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace
from uuid import uuid4

from app.services.surveys import SurveyResponseGenerator


class DummyPersona:
    """Mock modelu Persona."""

    def __init__(self, name="Alice"):
        self.id = str(uuid4())
        self.full_name = name
        self.age = 28
        self.gender = "female"
        self.location = "Warsaw"
        self.education_level = "Master"
        self.income_bracket = "50k-70k"
        self.occupation = "Designer"
        self.background_story = "Creative professional who values quality design."
        self.values = ["Creativity", "Innovation"]
        self.interests = ["Design", "Art"]


@pytest.fixture
def service(mock_llm):
    """Tworzy instancję serwisu z mock LLM."""
    from unittest.mock import patch

    # Configure mock_llm to return different responses based on question type
    async def smart_ainvoke(messages):
        messages_str = str(messages)
        if "scale" in messages_str.lower() or "rating" in messages_str.lower():
            return SimpleNamespace(content="4")
        elif "yes" in messages_str.lower() or "no" in messages_str.lower():
            return SimpleNamespace(content="Yes")
        elif "choose one" in messages_str.lower():
            return SimpleNamespace(content="Option 1")
        elif "comma-separated" in messages_str.lower():
            return SimpleNamespace(content="Option 1, Option 2")
        else:
            return SimpleNamespace(content="This is a thoughtful open-ended response based on my background.")

    mock_llm.ainvoke.side_effect = smart_ainvoke

    with patch('app.services.surveys.survey_response_generator.get_settings') as mock_settings:
        mock_settings.return_value.DEFAULT_MODEL = "gemini-2.5-flash"
        mock_settings.return_value.GOOGLE_API_KEY = "test_key"
        mock_settings.return_value.TEMPERATURE = 0.7

        svc = SurveyResponseGenerator()
        svc.llm = mock_llm
        return svc


@pytest.fixture
def mock_db():
    """Tworzy mock sesji bazodanowej."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_load_project_personas(service, mock_db):
    """Test ładowania person przypisanych do projektu."""
    project_id = str(uuid4())
    personas = [DummyPersona("Alice"), DummyPersona("Bob"), DummyPersona("Charlie")]

    # Mock wyniku query
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = personas
    mock_db.execute.return_value = mock_result

    loaded = await service._load_project_personas(mock_db, project_id)

    assert len(loaded) == 3
    assert loaded[0].full_name == "Alice"


# Testy LangChain prompt/chain wymagają zbyt dużo mock'owania - pomijamy je
# Testujemy tylko publiczne API i helper methods


def test_build_persona_context(service):
    """Test budowania kontekstu persony."""
    persona = DummyPersona("Alice")

    context = service._build_persona_context(persona)

    assert isinstance(context, str)
    assert "Alice" in context or str(persona.age) in context
    assert "Designer" in context or persona.occupation in context


def test_calculate_question_stats_single_choice(service):
    """Test obliczania statystyk dla pytania single-choice."""
    question_type = "single-choice"
    answers = ["Option 1", "Option 2", "Option 1", "Option 3", "Option 1"]

    stats = service._calculate_question_stats(question_type, answers)

    assert "distribution" in stats
    assert "most_common" in stats
    assert stats["distribution"]["Option 1"] == 3
    assert stats["most_common"] == "Option 1"


def test_calculate_question_stats_multiple_choice(service):
    """Test obliczania statystyk dla pytania multiple-choice."""
    question_type = "multiple-choice"
    answers = [
        ["Option 1", "Option 2"],
        ["Option 1", "Option 3"],
        ["Option 2", "Option 3"]
    ]

    stats = service._calculate_question_stats(question_type, answers)

    assert "distribution" in stats
    assert "most_common" in stats
    # Option 1, 2, 3 powinny być policzone
    assert stats["distribution"]["Option 1"] == 2


def test_calculate_question_stats_rating_scale(service):
    """Test obliczania statystyk dla pytania rating-scale."""
    question_type = "rating-scale"
    answers = [4, 5, 3, 4, 5, 4]

    stats = service._calculate_question_stats(question_type, answers)

    assert "mean" in stats
    assert "median" in stats
    assert "distribution" in stats
    assert stats["mean"] > 3
    assert stats["mean"] < 5


def test_calculate_question_stats_open_text(service):
    """Test obliczania statystyk dla pytania open-text."""
    question_type = "open-text"
    answers = [
        "This is a great product.",
        "I love the design and features.",
        "Too expensive."
    ]

    stats = service._calculate_question_stats(question_type, answers)

    assert "total_responses" in stats
    assert "avg_word_count" in stats
    assert "sample_responses" in stats
    assert stats["total_responses"] == 3


def test_calculate_demographic_breakdown(service):
    """Test obliczania rozkładu demograficznego."""
    from app.models.survey import SurveyResponse

    personas = {
        uuid4(): DummyPersona("Alice"),
        uuid4(): DummyPersona("Bob"),
        uuid4(): DummyPersona("Charlie")
    }

    # Ustawiamy różne wartości demograficzne
    personas_list = list(personas.values())
    personas_list[0].age = 25
    personas_list[0].gender = "female"
    personas_list[1].age = 35
    personas_list[1].gender = "male"
    personas_list[2].age = 45
    personas_list[2].gender = "male"

    # Mock responses
    responses = []
    for persona_id, persona in personas.items():
        response = MagicMock()
        response.persona_id = persona_id
        responses.append(response)

    # Rebuild personas dict with proper keys
    personas_dict = {response.persona_id: personas_list[i] for i, response in enumerate(responses)}

    breakdown = service._calculate_demographic_breakdown(responses, personas_dict, [])

    assert "by_age" in breakdown
    assert "by_gender" in breakdown
    assert len(breakdown["by_age"]) > 0
    assert len(breakdown["by_gender"]) > 0


@pytest.mark.asyncio
async def test_empty_personas_handling(service, mock_db):
    """Test obsługi przypadku gdy brak person w projekcie."""
    project_id = str(uuid4())

    # Mock zwracający pustą listę
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    personas = await service._load_project_personas(mock_db, project_id)
    assert len(personas) == 0


def test_pizza_fallback_response(service):
    """Test deterministycznego fallbacku dla pytania o pizzę."""
    persona = DummyPersona("Alice")
    persona.values = ["Health", "Wellness"]

    response = service._pizza_fallback_response(persona)

    assert isinstance(response, str)
    assert len(response) > 0
    assert "pizza" in response.lower() or "Alice" in response
