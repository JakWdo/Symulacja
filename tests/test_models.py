"""Testy jednostkowe dla modeli bazy danych."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.project import Project
from app.models.persona import Persona
from app.models.focus_group import FocusGroup
from app.models.persona_events import PersonaResponse, PersonaEvent
from app.models.survey import Survey, SurveyResponse


class TestProjectModel:
    """Testy modelu Project."""

    def test_project_creation(self):
        """Test tworzenia instancji projektu."""
        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Test Project",
            description="Testing new product",
            target_demographics={
                "age_group": {"18-24": 0.3, "25-34": 0.7},
                "gender": {"male": 0.5, "female": 0.5}
            },
            target_sample_size=20
        )

        assert project.name == "Test Project"
        assert project.target_sample_size == 20
        assert project.is_active is True
        assert project.is_statistically_valid is False


    def test_project_demographics_structure(self):
        """Test struktury rozkładów demograficznych."""
        demographics = {
            "age_group": {"18-24": 0.2, "25-34": 0.3, "35-44": 0.5},
            "gender": {"male": 0.6, "female": 0.4},
            "education_level": {
                "high_school": 0.2,
                "bachelors": 0.5,
                "masters": 0.3
            }
        }

        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Demographics Test",
            target_demographics=demographics,
            target_sample_size=50
        )

        assert "age_group" in project.target_demographics
        assert "gender" in project.target_demographics
        assert sum(project.target_demographics["age_group"].values()) == pytest.approx(1.0)


    def test_project_validation_fields(self):
        """Test pól związanych z walidacją statystyczną."""
        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Validation Test",
            target_demographics={"age_group": {"18-24": 1.0}},
            target_sample_size=10,
            chi_square_statistic={"age": 2.5, "gender": 1.2},
            p_values={"age": 0.67, "gender": 0.89},
            is_statistically_valid=True,
            validation_date=datetime.now(timezone.utc)
        )

        assert project.is_statistically_valid is True
        assert "age" in project.chi_square_statistic
        assert project.p_values["age"] > 0.05  # p > 0.05 = valid


    def test_project_repr(self):
        """Test reprezentacji string projektu."""
        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Repr Test",
            target_demographics={},
            target_sample_size=10
        )

        repr_str = repr(project)
        assert "Project" in repr_str
        assert "Repr Test" in repr_str


class TestPersonaModel:
    """Testy modelu Persona."""

    def test_persona_creation(self):
        """Test tworzenia instancji persony."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=30,
            gender="female",
            location="Warsaw",
            education_level="Master",
            income_bracket="50k-70k",
            occupation="Designer",
            full_name="Anna Kowalska",
            background_story="Creative professional who loves design."
        )

        assert persona.age == 30
        assert persona.gender == "female"
        assert persona.full_name == "Anna Kowalska"
        assert persona.is_active is True


    def test_persona_big_five_traits(self):
        """Test cech osobowości Big Five."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=25,
            gender="male",
            openness=0.8,
            conscientiousness=0.6,
            extraversion=0.7,
            agreeableness=0.75,
            neuroticism=0.3
        )

        # Wszystkie wartości powinny być w zakresie 0-1
        assert 0.0 <= persona.openness <= 1.0
        assert 0.0 <= persona.conscientiousness <= 1.0
        assert 0.0 <= persona.extraversion <= 1.0
        assert 0.0 <= persona.agreeableness <= 1.0
        assert 0.0 <= persona.neuroticism <= 1.0


    def test_persona_hofstede_dimensions(self):
        """Test wymiarów kulturowych Hofstede."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=40,
            gender="female",
            power_distance=0.5,
            individualism=0.7,
            masculinity=0.4,
            uncertainty_avoidance=0.6,
            long_term_orientation=0.8,
            indulgence=0.6
        )

        # Sprawdzamy zakres wartości
        assert 0.0 <= persona.power_distance <= 1.0
        assert 0.0 <= persona.individualism <= 1.0
        assert 0.0 <= persona.indulgence <= 1.0


    def test_persona_values_and_interests(self):
        """Test wartości i zainteresowań persony."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=28,
            gender="non-binary",
            values=["Innovation", "Creativity", "Family"],
            interests=["Photography", "Travel", "Yoga"]
        )

        assert len(persona.values) == 3
        assert "Innovation" in persona.values
        assert len(persona.interests) == 3
        assert "Photography" in persona.interests


    def test_persona_repr(self):
        """Test reprezentacji string persony."""
        project_id = uuid4()
        persona = Persona(
            id=uuid4(),
            project_id=project_id,
            age=30,
            gender="male"
        )

        repr_str = repr(persona)
        assert "Persona" in repr_str
        assert str(project_id) in repr_str


class TestFocusGroupModel:
    """Testy modelu FocusGroup."""

    def test_focus_group_creation(self):
        """Test tworzenia grupy fokusowej."""
        persona_ids = [uuid4(), uuid4(), uuid4()]
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Product Feedback",
            description="Gathering user feedback",
            persona_ids=persona_ids,
            questions=["What do you think?", "Would you buy it?"],
            mode="normal",
            status="pending"
        )

        assert focus_group.name == "Product Feedback"
        assert len(focus_group.persona_ids) == 3
        assert len(focus_group.questions) == 2
        assert focus_group.status == "pending"


    def test_focus_group_performance_metrics(self):
        """Test metryk wydajności grupy fokusowej."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Performance Test",
            persona_ids=[uuid4()],
            questions=["Q1?"],
            total_execution_time_ms=25000,  # 25 sekund
            avg_response_time_ms=2500.0     # 2.5 sekundy
        )

        assert focus_group.total_execution_time_ms == 25000
        assert focus_group.avg_response_time_ms == 2500.0


    def test_focus_group_meets_performance_requirements_success(self):
        """Test sprawdzania wymagań wydajnościowych - sukces."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Fast Group",
            persona_ids=[uuid4()],
            questions=["Q?"],
            total_execution_time_ms=20000,  # 20s < 30s ✓
            avg_response_time_ms=2000.0     # 2s < 3s ✓
        )

        assert focus_group.meets_performance_requirements() is True


    def test_focus_group_meets_performance_requirements_failure(self):
        """Test sprawdzania wymagań wydajnościowych - niepowodzenie."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Slow Group",
            persona_ids=[uuid4()],
            questions=["Q?"],
            total_execution_time_ms=35000,  # 35s > 30s ✗
            avg_response_time_ms=3500.0     # 3.5s > 3s ✗
        )

        assert focus_group.meets_performance_requirements() is False


    def test_focus_group_status_transitions(self):
        """Test przejść statusów grupy fokusowej."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Status Test",
            persona_ids=[uuid4()],
            questions=["Q?"],
            status="pending"
        )

        assert focus_group.status == "pending"

        # Symulacja rozpoczęcia
        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        assert focus_group.status == "running"
        assert focus_group.started_at is not None

        # Symulacja zakończenia
        focus_group.status = "completed"
        focus_group.completed_at = datetime.now(timezone.utc)
        assert focus_group.status == "completed"
        assert focus_group.completed_at is not None


    def test_focus_group_adversarial_mode(self):
        """Test trybu adversarial grupy fokusowej."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Adversarial Test",
            persona_ids=[uuid4()],
            questions=["Q?"],
            mode="adversarial"
        )

        assert focus_group.mode == "adversarial"


class TestPersonaResponseModel:
    """Testy modelu PersonaResponse."""

    def test_persona_response_creation(self):
        """Test tworzenia odpowiedzi persony."""
        response = PersonaResponse(
            id=uuid4(),
            focus_group_id=uuid4(),
            persona_id=uuid4(),
            question="What do you think?",
            response="I think it's a great idea with innovative features."
        )

        assert response.question == "What do you think?"
        assert "great idea" in response.response


class TestPersonaEventModel:
    """Testy modelu PersonaEvent (event sourcing)."""

    def test_persona_event_creation(self):
        """Test tworzenia eventu persony."""
        event = PersonaEvent(
            id=uuid4(),
            persona_id=uuid4(),
            focus_group_id=uuid4(),
            event_type="question_asked",
            event_data={"question": "What do you think?"},
            sequence_number=1
        )

        assert event.event_type == "question_asked"
        assert event.sequence_number == 1
        assert "question" in event.event_data


    def test_persona_event_with_embedding(self):
        """Test eventu z embeddingiem dla semantic search."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]  # Przykładowy wektor

        event = PersonaEvent(
            id=uuid4(),
            persona_id=uuid4(),
            focus_group_id=uuid4(),
            event_type="response_given",
            event_data={
                "question": "Rate this",
                "response": "I rate it highly"
            },
            sequence_number=2,
            embedding=embedding
        )

        assert event.embedding is not None
        assert len(event.embedding) == 5


class TestSurveyModel:
    """Testy modelu Survey."""

    def test_survey_creation(self):
        """Test tworzenia ankiety."""
        survey = Survey(
            id=uuid4(),
            project_id=uuid4(),
            title="Customer Satisfaction",
            description="Measuring satisfaction",
            questions=[
                {
                    "id": "q1",
                    "text": "Rate satisfaction (1-5)",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"]
                }
            ],
            status="pending"
        )

        assert survey.title == "Customer Satisfaction"
        assert len(survey.questions) == 1
        assert survey.questions[0]["type"] == "scale"


class TestSurveyResponseModel:
    """Testy modelu SurveyResponse."""

    def test_survey_response_creation(self):
        """Test tworzenia odpowiedzi na ankietę."""
        response = SurveyResponse(
            id=uuid4(),
            survey_id=uuid4(),
            persona_id=uuid4(),
            question_id="q1",
            answer="5"
        )

        assert response.question_id == "q1"
        assert response.answer == "5"
        assert response.answers == {"q1": "5"}

    def test_survey_response_multi_question_mapping(self):
        """Test odwzorowania wielu odpowiedzi w dodatkowych polach."""

        response = SurveyResponse(
            id=uuid4(),
            survey_id=uuid4(),
            persona_id=uuid4(),
            answers={"q1": "A", "q2": "B"}
        )

        assert response.question_id is None
        assert response.answer is None
        assert response.answers == {"q1": "A", "q2": "B"}


class TestModelRelationships:
    """Testy relacji między modelami."""

    def test_project_has_personas_relationship(self):
        """Test relacji Project -> Personas."""
        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Test",
            target_demographics={},
            target_sample_size=10
        )

        # Relacja powinna istnieć
        assert hasattr(project, "personas")
        assert hasattr(project, "focus_groups")


    def test_persona_has_responses_relationship(self):
        """Test relacji Persona -> PersonaResponse."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=30,
            gender="female"
        )

        # Relacja powinna istnieć
        assert hasattr(persona, "responses")
        assert hasattr(persona, "events")


    def test_focus_group_has_responses_relationship(self):
        """Test relacji FocusGroup -> PersonaResponse."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test",
            persona_ids=[],
            questions=[]
        )

        # Relacja powinna istnieć
        assert hasattr(focus_group, "responses")


class TestModelDefaults:
    """Testy wartości domyślnych modeli."""

    def test_project_default_values(self):
        """Test domyślnych wartości projektu."""
        project = Project(
            id=uuid4(),
            owner_id=uuid4(),
            name="Test",
            target_demographics={},
            target_sample_size=10
        )

        assert project.is_active is True
        assert project.is_statistically_valid is False


    def test_persona_default_values(self):
        """Test domyślnych wartości persony."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=30,
            gender="male"
        )

        assert persona.is_active is True


    def test_focus_group_default_values(self):
        """Test domyślnych wartości grupy fokusowej."""
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test",
            persona_ids=[],
            questions=[]
        )

        assert focus_group.status == "pending"
        assert focus_group.mode == "normal"


class TestModelConstraints:
    """Testy ograniczeń i walidacji modeli."""

    def test_big_five_range_validation(self):
        """Test czy wartości Big Five są w zakresie 0-1."""
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=30,
            gender="male",
            openness=0.8,
            neuroticism=0.2
        )

        # W produkcji można dodać walidatory Pydantic/SQLAlchemy
        assert 0 <= persona.openness <= 1
        assert 0 <= persona.neuroticism <= 1
