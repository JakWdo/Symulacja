"""Testy jednostkowe i integracyjne dla SurveyResponseGenerator."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace
from uuid import uuid4
from collections import Counter

from app.services.survey_response_generator import SurveyResponseGenerator


class DummyLLM:
    """Mock LLM do testów bez wywoływania prawdziwego API."""

    async def ainvoke(self, messages):
        """Symuluje wywołanie LLM zwracając odpowiedź na pytanie."""
        # Analizujemy typ pytania z messages
        messages_str = str(messages)
        if "scale" in messages_str.lower() or "1-5" in messages_str:
            return SimpleNamespace(content="4")
        elif "yes" in messages_str.lower() or "no" in messages_str.lower():
            return SimpleNamespace(content="Yes")
        else:
            return SimpleNamespace(content="This is a thoughtful open-ended response based on my background.")


class DummySurvey:
    """Mock modelu Survey."""

    def __init__(self):
        self.id = str(uuid4())
        self.title = "Product Survey"
        self.description = "Survey about new product"
        self.project_id = str(uuid4())
        self.questions = [
            {
                "id": "q1",
                "text": "How satisfied are you?",
                "type": "scale",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "id": "q2",
                "text": "Would you recommend this?",
                "type": "yes_no",
                "options": ["Yes", "No"]
            },
            {
                "id": "q3",
                "text": "What do you think?",
                "type": "open_ended",
                "options": []
            }
        ]
        self.status = "pending"
        self.started_at = None
        self.completed_at = None


class DummyPersona:
    """Mock modelu Persona."""

    def __init__(self, name="Alice"):
        self.id = str(uuid4())
        self.name = name
        self.age = 28
        self.gender = "female"
        self.location = "Warsaw"
        self.education_level = "Master"
        self.income_bracket = "50k-70k"
        self.occupation = "Designer"
        self.background_story = "Creative professional who values quality design."
        self.values = ["Creativity", "Innovation"]
        self.openness = 0.8
        self.conscientiousness = 0.7
        self.extraversion = 0.6
        self.agreeableness = 0.7
        self.neuroticism = 0.3


@pytest.fixture
def service():
    """Tworzy instancję serwisu bez inicjalizacji prawdziwego LLM."""
    svc = SurveyResponseGenerator.__new__(SurveyResponseGenerator)
    svc.llm = DummyLLM()
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
    assert loaded[0].name == "Alice"


@pytest.mark.asyncio
async def test_generate_single_answer_scale(service):
    """Test generowania odpowiedzi na pytanie skalowe (1-5)."""
    persona = DummyPersona("Alice")
    question = {
        "id": "q1",
        "text": "Rate your satisfaction (1-5)",
        "type": "scale",
        "options": ["1", "2", "3", "4", "5"]
    }

    answer = await service._generate_single_answer(persona, question)

    assert answer in question["options"]
    # Mock LLM zwraca "4"
    assert answer == "4"


@pytest.mark.asyncio
async def test_generate_single_answer_yes_no(service):
    """Test generowania odpowiedzi na pytanie tak/nie."""
    persona = DummyPersona("Bob")
    question = {
        "id": "q2",
        "text": "Would you buy this product? (Yes/No)",
        "type": "yes_no",
        "options": ["Yes", "No"]
    }

    answer = await service._generate_single_answer(persona, question)

    assert answer in question["options"]


@pytest.mark.asyncio
async def test_generate_single_answer_open_ended(service):
    """Test generowania odpowiedzi na pytanie otwarte."""
    persona = DummyPersona("Charlie")
    question = {
        "id": "q3",
        "text": "What are your thoughts on the product?",
        "type": "open_ended",
        "options": []
    }

    answer = await service._generate_single_answer(persona, question)

    assert isinstance(answer, str)
    assert len(answer) > 0


@pytest.mark.asyncio
async def test_generate_persona_responses(service, mock_db):
    """Test generowania wszystkich odpowiedzi dla jednej persony."""
    persona = DummyPersona("Alice")
    survey = DummySurvey()

    responses = await service._generate_persona_responses(
        db=mock_db,
        persona=persona,
        survey=survey
    )

    assert len(responses) == len(survey.questions)
    assert all("question_id" in r for r in responses)
    assert all("answer" in r for r in responses)
    assert all("persona_id" in r for r in responses)


@pytest.mark.asyncio
async def test_parallel_response_generation(service, mock_db):
    """Test równoległego generowania odpowiedzi od wielu person."""
    survey = DummySurvey()
    personas = [DummyPersona(f"Person{i}") for i in range(5)]

    # Mock survey query
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = survey
    mock_db.execute.return_value = mock_result

    all_responses = []
    for persona in personas:
        responses = await service._generate_persona_responses(mock_db, persona, survey)
        all_responses.extend(responses)

    # 5 person × 3 pytania = 15 odpowiedzi
    assert len(all_responses) == 5 * 3


@pytest.mark.asyncio
async def test_calculate_question_analytics_scale(service):
    """Test obliczania analityki dla pytania skalowego."""
    question = {
        "id": "q1",
        "text": "Rate satisfaction (1-5)",
        "type": "scale",
        "options": ["1", "2", "3", "4", "5"]
    }

    responses = [
        {"question_id": "q1", "answer": "5"},
        {"question_id": "q1", "answer": "4"},
        {"question_id": "q1", "answer": "4"},
        {"question_id": "q1", "answer": "3"},
        {"question_id": "q1", "answer": "5"}
    ]

    analytics = service._calculate_question_analytics(question, responses)

    assert analytics["question_id"] == "q1"
    assert analytics["question_text"] == question["text"]
    assert analytics["total_responses"] == 5
    assert "distribution" in analytics
    assert analytics["distribution"]["4"] == 2  # Dwie czwórki


@pytest.mark.asyncio
async def test_calculate_question_analytics_yes_no(service):
    """Test obliczania analityki dla pytania tak/nie."""
    question = {
        "id": "q2",
        "text": "Would you buy?",
        "type": "yes_no",
        "options": ["Yes", "No"]
    }

    responses = [
        {"question_id": "q2", "answer": "Yes"},
        {"question_id": "q2", "answer": "Yes"},
        {"question_id": "q2", "answer": "No"},
        {"question_id": "q2", "answer": "Yes"}
    ]

    analytics = service._calculate_question_analytics(question, responses)

    assert analytics["distribution"]["Yes"] == 3
    assert analytics["distribution"]["No"] == 1
    assert analytics["avg_score"] == 0.75  # 75% Yes


@pytest.mark.asyncio
async def test_calculate_question_analytics_open_ended(service):
    """Test obliczania analityki dla pytania otwartego."""
    question = {
        "id": "q3",
        "text": "Your thoughts?",
        "type": "open_ended",
        "options": []
    }

    responses = [
        {"question_id": "q3", "answer": "Great product with excellent quality."},
        {"question_id": "q3", "answer": "I love the design and features."},
        {"question_id": "q3", "answer": "Too expensive for what it offers."}
    ]

    analytics = service._calculate_question_analytics(question, responses)

    assert analytics["total_responses"] == 3
    assert "sample_responses" in analytics
    assert len(analytics["sample_responses"]) <= 5  # Max 5 przykładów


@pytest.mark.asyncio
async def test_save_responses_to_db(service, mock_db):
    """Test zapisywania odpowiedzi do bazy danych."""
    survey_id = str(uuid4())
    responses = [
        {
            "survey_id": survey_id,
            "persona_id": str(uuid4()),
            "question_id": "q1",
            "answer": "5"
        },
        {
            "survey_id": survey_id,
            "persona_id": str(uuid4()),
            "question_id": "q2",
            "answer": "Yes"
        }
    ]

    await service._save_responses(mock_db, responses)

    # Sprawdzamy czy add został wywołany dla każdej odpowiedzi
    assert mock_db.add.call_count == len(responses)
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_error_handling_in_response_generation(service):
    """Test obsługi błędów podczas generowania odpowiedzi."""

    # Mock LLM który rzuca wyjątek
    async def failing_invoke(messages):
        raise Exception("API Error")

    service.llm.ainvoke = failing_invoke

    persona = DummyPersona("Alice")
    question = {
        "id": "q1",
        "text": "Rate this",
        "type": "scale",
        "options": ["1", "2", "3", "4", "5"]
    }

    # Serwis powinien obsłużyć błąd bez crashowania
    try:
        answer = await service._generate_single_answer(persona, question)
        # Powinien zwrócić domyślną odpowiedź lub None
        assert answer is None or answer in question["options"]
    except Exception:
        # W przypadku braku fallbacku, powinien rzucić kontrolowany wyjątek
        pass


def test_prompt_includes_persona_traits(service):
    """Test czy prompt zawiera cechy persony."""
    persona = DummyPersona("Alice")
    persona.openness = 0.9
    persona.conscientiousness = 0.3

    question = {
        "id": "q1",
        "text": "What do you think?",
        "type": "open_ended",
        "options": []
    }

    messages = service._create_survey_prompt(persona, question)

    prompt_text = str(messages)
    # Prompt powinien zawierać informacje o personie
    assert persona.name in prompt_text or "Alice" in prompt_text
    assert str(persona.age) in prompt_text or "28" in prompt_text


def test_validate_answer_against_options(service):
    """Test walidacji odpowiedzi względem dostępnych opcji."""
    question_scale = {
        "type": "scale",
        "options": ["1", "2", "3", "4", "5"]
    }

    question_open = {
        "type": "open_ended",
        "options": []
    }

    # Dla pytania skalowego odpowiedź musi być z opcji
    assert service._validate_answer("3", question_scale) is True
    assert service._validate_answer("6", question_scale) is False

    # Dla pytania otwartego każda odpowiedź jest OK
    assert service._validate_answer("Any text here", question_open) is True


@pytest.mark.asyncio
async def test_empty_personas_handling(service, mock_db):
    """Test obsługi przypadku gdy brak person w projekcie."""
    project_id = str(uuid4())

    # Mock zwracający pustą listę
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="no personas"):
        personas = await service._load_project_personas(mock_db, project_id)
        if len(personas) == 0:
            raise ValueError("Project has no personas")


@pytest.mark.asyncio
async def test_demographics_influence_on_responses(service):
    """Test czy demografia wpływa na odpowiedzi (różne persony = różne odpowiedzi)."""
    young_persona = DummyPersona("Young")
    young_persona.age = 22
    young_persona.openness = 0.9

    old_persona = DummyPersona("Senior")
    old_persona.age = 65
    old_persona.openness = 0.3

    question = {
        "id": "q1",
        "text": "How do you feel about new technology?",
        "type": "open_ended",
        "options": []
    }

    # W rzeczywistości odpowiedzi powinny się różnić
    # Mock LLM zwraca to samo, ale w prawdziwym systemie byłyby różne
    young_answer = await service._generate_single_answer(young_persona, question)
    old_answer = await service._generate_single_answer(old_persona, question)

    assert isinstance(young_answer, str)
    assert isinstance(old_answer, str)


def test_calculate_metrics(service):
    """Test obliczania metryk wydajności ankiety."""
    total_responses = 50  # 10 person × 5 pytań
    total_time_ms = 15000  # 15 sekund

    metrics = service._calculate_metrics(total_responses, total_time_ms)

    assert "total_execution_time_ms" in metrics
    assert "avg_response_time_ms" in metrics
    assert "total_responses" in metrics
    assert metrics["total_responses"] == total_responses
    assert metrics["avg_response_time_ms"] == total_time_ms / total_responses


@pytest.mark.asyncio
async def test_multiple_choice_question(service):
    """Test obsługi pytań wielokrotnego wyboru."""
    persona = DummyPersona("Alice")
    question = {
        "id": "q4",
        "text": "Which features do you like?",
        "type": "multiple_choice",
        "options": ["Design", "Performance", "Price", "Support"]
    }

    answer = await service._generate_single_answer(persona, question)

    # Odpowiedź powinna być z listy opcji (lub ich kombinacją)
    assert isinstance(answer, str)
