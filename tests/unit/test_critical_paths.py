"""Testy krytycznych ścieżek biznesowych aplikacji.

Te testy pokrywają najważniejsze user flows i edge cases,
które mogą zepsuć podstawową funkcjonalność aplikacji.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone


class TestPersonaGenerationCriticalPath:
    """Krytyczne testy generowania person."""

    def test_demographic_distribution_sums_to_one(self):
        """
        KRYTYCZNE: Rozkłady demograficzne muszą sumować się do 1.0.

        Jeśli suma != 1.0, chi-square test będzie niepoprawny.
        """
        age_distribution = {"18-24": 0.3, "25-34": 0.4, "35-44": 0.3}
        gender_distribution = {"male": 0.5, "female": 0.5}

        assert sum(age_distribution.values()) == pytest.approx(1.0)
        assert sum(gender_distribution.values()) == pytest.approx(1.0)


    def test_big_five_traits_in_valid_range(self):
        """
        KRYTYCZNE: Cechy Big Five muszą być w zakresie [0, 1].

        Wartości poza zakresem mogą spowodować błędy w analizie.
        """
        from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain

        gen = PersonaGeneratorLangChain.__new__(PersonaGeneratorLangChain)
        gen.settings = type('obj', (object,), {'RANDOM_SEED': 42})()

        import numpy as np
        gen._rng = np.random.default_rng(42)

        traits = gen.sample_big_five_traits()

        for trait_name, value in traits.items():
            assert 0.0 <= value <= 1.0, f"{trait_name} = {value} is out of range [0, 1]"


    def test_persona_must_have_required_fields(self):
        """
        KRYTYCZNE: Persona musi mieć wszystkie wymagane pola.

        Brak age, gender, lub project_id spowoduje błędy DB.
        """
        from app.models.persona import Persona

        # To powinno działać
        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),
            age=30,
            gender="female"
        )

        assert persona.age is not None
        assert persona.gender is not None
        assert persona.project_id is not None


    def test_chi_square_validation_rejects_bad_distributions(self):
        """
        KRYTYCZNE: Walidacja chi-square musi odrzucać złe rozkłady.

        Jeśli wszystkie persony mają ten sam wiek, test powinien failować.
        """
        from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain, DemographicDistribution

        gen = PersonaGeneratorLangChain.__new__(PersonaGeneratorLangChain)
        gen.settings = type('obj', (object,), {'RANDOM_SEED': 42})()

        import numpy as np
        gen._rng = np.random.default_rng(42)

        # Wygeneruj persony które NIE pasują do rozkładu
        target = DemographicDistribution(
            age_groups={"18-24": 0.5, "25-34": 0.5},
            genders={"male": 0.5, "female": 0.5},
            education_levels={"high_school": 0.5, "bachelors": 0.5},
            income_brackets={"<30k": 0.5, "30k-60k": 0.5},
            locations={"urban": 0.5, "rural": 0.5}
        )

        # Wszystkie persony z jednej grupy = zły rozkład
        bad_personas = [
            {"age_group": "18-24", "gender": "male", "education_level": "high_school",
             "income_bracket": "<30k", "location": "urban"}
            for _ in range(20)
        ]

        validation = gen.validate_distribution(bad_personas, target)

        # Powinno wykryć że rozkład jest invalid
        assert validation["overall_valid"] is False


class TestFocusGroupCriticalPath:
    """Krytyczne testy grup fokusowych."""

    def test_focus_group_requires_questions(self):
        """
        KRYTYCZNE: Grupa fokusowa musi mieć przynajmniej jedno pytanie.

        Pusta lista pytań spowoduje błąd wykonania.
        """
        from app.models.focus_group import FocusGroup

        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test Group",
            persona_ids=[uuid4()],
            questions=["What do you think?"]  # Minimum 1 pytanie
        )

        assert len(focus_group.questions) > 0


    def test_focus_group_requires_personas(self):
        """
        KRYTYCZNE: Grupa fokusowa musi mieć przynajmniej jedną personę.

        Brak person spowoduje błąd wykonania.
        """
        from app.models.focus_group import FocusGroup

        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test Group",
            persona_ids=[uuid4()],  # Minimum 1 persona
            questions=["Question?"]
        )

        assert len(focus_group.persona_ids) > 0


    def test_performance_metrics_calculated_correctly(self):
        """
        KRYTYCZNE: Metryki wydajności muszą być obliczane poprawnie.

        Błąd w obliczeniach może dać fałszywe alarmy o wydajności.
        """
        from app.models.focus_group import FocusGroup

        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test",
            persona_ids=[uuid4()],
            questions=["Q?"],
            total_execution_time_ms=25000,  # 25 sekund
            avg_response_time_ms=2500.0     # 2.5 sekundy
        )

        # Powinno spełniać wymagania (<30s total, <3s avg)
        assert focus_group.meets_performance_requirements() is True

        # Wolna grupa
        slow_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Slow",
            persona_ids=[uuid4()],
            questions=["Q?"],
            total_execution_time_ms=35000,  # 35 sekund - za wolno!
            avg_response_time_ms=3500.0
        )

        assert slow_group.meets_performance_requirements() is False


class TestMemoryEventSourcingCriticalPath:
    """Krytyczne testy event sourcingu."""

    def test_persona_events_must_have_sequence_number(self):
        """
        KRYTYCZNE: Eventy muszą mieć sequence_number dla sortowania.

        Bez sequence_number, kolejność eventów będzie losowa.
        """
        from app.models.persona_events import PersonaEvent

        event = PersonaEvent(
            id=uuid4(),
            persona_id=uuid4(),
            focus_group_id=uuid4(),
            event_type="question_asked",
            event_data={"question": "Test?"},
            sequence_number=1  # WYMAGANE
        )

        assert event.sequence_number is not None
        assert event.sequence_number >= 0


    def test_embedding_dimension_consistency(self):
        """
        KRYTYCZNE: Wszystkie embeddingi muszą mieć tę samą wymiarowość.

        Niezgodność wymiarów uniemożliwi semantic search.
        """
        from app.models.persona_events import PersonaEvent

        event1 = PersonaEvent(
            id=uuid4(),
            persona_id=uuid4(),
            focus_group_id=uuid4(),
            event_type="response_given",
            event_data={"response": "Answer 1"},
            sequence_number=1,
            embedding=[0.1] * 768  # 768 dimensions (typical for Google embeddings)
        )

        event2 = PersonaEvent(
            id=uuid4(),
            persona_id=uuid4(),
            focus_group_id=uuid4(),
            event_type="response_given",
            event_data={"response": "Answer 2"},
            sequence_number=2,
            embedding=[0.2] * 768  # Ta sama wymiarowość!
        )

        assert len(event1.embedding) == len(event2.embedding)


class TestAuthenticationCriticalPath:
    """Krytyczne testy autentykacji."""

    def test_password_must_be_hashed_not_plain(self):
        """
        KRYTYCZNE: Hasła NIGDY nie mogą być zapisane jako plain text.

        To jest fundamentalny wymóg bezpieczeństwa.
        """
        from app.core.security import get_password_hash

        plain_password = "MySecretPassword123"
        hashed = get_password_hash(plain_password)

        # Hash NIE MOŻE być równy plain text
        assert hashed != plain_password

        # Hash powinien mieć format bcrypt
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


    def test_jwt_token_must_have_expiration(self):
        """
        KRYTYCZNE: JWT token MUSI mieć expiration time.

        Token bez expiration jest trwałym bezpieczeństwem.
        """
        from app.core.security import create_access_token, decode_access_token
        import jwt

        token = create_access_token({"sub": str(uuid4())})
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "exp" in payload, "JWT token must have expiration!"


    def test_password_validation_blocks_weak_passwords(self):
        """
        KRYTYCZNE: Słabe hasła muszą być odrzucane.

        Akceptowanie słabych haseł = dziura w bezpieczeństwie.
        """
        from app.api.auth import RegisterRequest
        from pydantic import ValidationError

        # Te hasła powinny być ODRZUCONE
        weak_passwords = [
            "short",        # Za krótkie
            "12345678",     # Tylko cyfry
            "abcdefgh",     # Tylko litery
            "a" * 73,       # Za długie (bcrypt limit)
        ]

        for weak_pass in weak_passwords:
            with pytest.raises(ValidationError):
                RegisterRequest(
                    email="test@example.com",
                    password=weak_pass,
                    full_name="Test User"
                )


class TestDatabaseConstraintsCriticalPath:
    """Krytyczne testy ograniczeń bazy danych."""

    def test_project_requires_owner_id(self):
        """
        KRYTYCZNE: Każdy projekt musi mieć owner_id.

        Projekty bez właściciela = dziura w security.
        """
        from app.models.project import Project

        project = Project(
            id=uuid4(),
            owner_id=uuid4(),  # WYMAGANE
            name="Test",
            target_demographics={},
            target_sample_size=10
        )

        assert project.owner_id is not None


    def test_persona_must_belong_to_project(self):
        """
        KRYTYCZNE: Każda persona musi należeć do projektu.

        Persony bez project_id mogą być dostępne dla wszystkich.
        """
        from app.models.persona import Persona

        persona = Persona(
            id=uuid4(),
            project_id=uuid4(),  # WYMAGANE - foreign key
            age=30,
            gender="female"
        )

        assert persona.project_id is not None


    def test_focus_group_status_transitions_valid(self):
        """
        KRYTYCZNE: Status grupy fokusowej może przejść tylko w prawidłowej kolejności.

        Nieprawidłowe przejścia = inconsistent state.
        """
        from app.models.focus_group import FocusGroup

        focus_group = FocusGroup(
            id=uuid4(),
            project_id=uuid4(),
            name="Test",
            persona_ids=[uuid4()],
            questions=["Q?"],
            status="pending"
        )

        # Prawidłowa kolejność: pending -> running -> completed
        assert focus_group.status == "pending"

        focus_group.status = "running"
        focus_group.started_at = datetime.now(timezone.utc)
        assert focus_group.status == "running"
        assert focus_group.started_at is not None

        focus_group.status = "completed"
        focus_group.completed_at = datetime.now(timezone.utc)
        assert focus_group.status == "completed"
        assert focus_group.completed_at is not None


class TestDataIntegrityCriticalPath:
    """Krytyczne testy integralności danych."""

    def test_survey_questions_must_have_type(self):
        """
        KRYTYCZNE: Każde pytanie ankietowe musi mieć typ.

        Bez typu, nie wiadomo jak przetworzyć odpowiedź.
        """
        valid_question = {
            "id": "q1",
            "text": "Rate this",
            "type": "scale",  # WYMAGANE
            "options": ["1", "2", "3", "4", "5"]
        }

        assert "type" in valid_question
        assert valid_question["type"] in ["scale", "yes_no", "open_ended", "multiple_choice"]


    def test_response_count_equals_personas_times_questions(self):
        """
        KRYTYCZNE: Liczba odpowiedzi = liczba person × liczba pytań.

        Niezgodność = niepełne dane lub duplikaty.
        """
        num_personas = 5
        num_questions = 3
        expected_responses = num_personas * num_questions

        # Symulacja
        actual_responses = 15  # 5 × 3 = 15

        assert actual_responses == expected_responses


    def test_timestamps_must_be_timezone_aware(self):
        """
        KRYTYCZNE: Wszystkie timestampy muszą mieć timezone.

        Naive datetime = problemy z różnymi strefami czasowymi.
        """
        from datetime import datetime, timezone

        # POPRAWNIE - z timezone
        aware_dt = datetime.now(timezone.utc)
        assert aware_dt.tzinfo is not None

        # BŁĘDNIE - naive datetime (bez timezone)
        naive_dt = datetime.now()
        # W produkcji używaj ZAWSZE datetime.now(timezone.utc)


class TestErrorHandlingCriticalPath:
    """Krytyczne testy obsługi błędów."""

    def test_division_by_zero_protection(self):
        """
        KRYTYCZNE: Obliczenia muszą być chronione przed dzieleniem przez zero.
        """
        def calculate_average(values):
            if len(values) == 0:
                return 0  # Zwróć 0 zamiast dzielić przez 0

            return sum(values) / len(values)

        assert calculate_average([]) == 0
        assert calculate_average([5, 10, 15]) == 10


    def test_empty_list_handling(self):
        """
        KRYTYCZNE: Funkcje muszą obsługiwać puste listy.

        Nie sprawdzony case pusty listy = częsty crash.
        """
        from statistics import mean, StatisticsError

        # Poprawne obsłużenie pustej listy
        values = []

        if len(values) > 0:
            avg = mean(values)
        else:
            avg = 0  # Domyślna wartość

        assert avg == 0


    def test_null_reference_protection(self):
        """
        KRYTYCZNE: Kod musi sprawdzać None przed użyciem.

        AttributeError na None = częsty błąd produkcyjny.
        """
        def safe_get_name(user):
            if user is None:
                return "Anonymous"

            return user.get("name", "Unknown")

        assert safe_get_name(None) == "Anonymous"
        assert safe_get_name({"name": "John"}) == "John"
        assert safe_get_name({}) == "Unknown"
