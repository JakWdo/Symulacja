"""
Testy jednostkowe dla PDFGenerator

Testuje generowanie raportów PDF dla projektów.
"""

import pytest
from app.services.export.pdf_generator import PDFGenerator


class TestPDFGenerator:
    """Testy dla generatora PDF."""

    @pytest.fixture
    def pdf_generator(self):
        """Fixture zwracający instancję PDFGenerator."""
        return PDFGenerator()

    @pytest.fixture
    def sample_project_data(self):
        """Fixture z przykładowymi danymi projektu."""
        return {
            "id": "test-project-id",
            "name": "Testowy Projekt",
            "description": "Opis testowego projektu",
            "target_audience": "Młodzi profesjonaliści",
            "research_objectives": "Zrozumienie potrzeb użytkowników",
            "is_statistically_valid": True,
            "personas": [
                {
                    "id": "persona-1",
                    "full_name": "Jan Kowalski",
                    "name": "Jan Kowalski",
                    "age": 28,
                    "gender": "male",
                    "occupation": "Software Developer",
                    "education_level": "Bachelor's Degree",
                    "location": "Warsaw",
                    "values": ["Innovation", "Growth"],
                    "interests": ["Technology", "Travel"],
                },
                {
                    "id": "persona-2",
                    "full_name": "Anna Nowak",
                    "name": "Anna Nowak",
                    "age": 32,
                    "gender": "female",
                    "occupation": "Product Manager",
                    "education_level": "Master's Degree",
                    "location": "Krakow",
                    "values": ["Family", "Success"],
                    "interests": ["Reading", "Yoga"],
                },
            ],
            "focus_groups": [
                {
                    "id": "fg-1",
                    "name": "Grupa Fokusowa 1",
                    "persona_ids": ["persona-1", "persona-2"],
                    "questions": ["Pytanie 1?", "Pytanie 2?"],
                    "ai_summary": {
                        "main_insights": "Kluczowe wnioski z dyskusji",
                        "key_themes": ["Temat 1", "Temat 2"],
                    },
                }
            ],
            "surveys": [
                {
                    "id": "survey-1",
                    "title": "Ankieta testowa",
                    "status": "completed",
                    "actual_responses": 50,
                    "target_responses": 100,
                }
            ],
        }

    @pytest.mark.asyncio
    async def test_generate_project_pdf_returns_bytes(
        self, pdf_generator, sample_project_data
    ):
        """Test generowania PDF - zwraca niepusty plik."""
        pdf_bytes = await pdf_generator.generate_project_pdf(
            project_data=sample_project_data,
            user_tier="free",
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF powinien zaczynać się od magicznych bajtów %PDF
        assert pdf_bytes[:4] == b"%PDF"

    @pytest.mark.asyncio
    async def test_generate_project_pdf_contains_project_name(
        self, pdf_generator, sample_project_data
    ):
        """Test czy PDF zawiera nazwę projektu."""
        pdf_bytes = await pdf_generator.generate_project_pdf(
            project_data=sample_project_data,
            user_tier="free",
        )

        # Konwertuj do stringa (może być w metadanych lub treści)
        pdf_string = pdf_bytes.decode("latin-1", errors="ignore")
        assert "Testowy Projekt" in pdf_string

    @pytest.mark.asyncio
    async def test_generate_project_pdf_with_full_personas(
        self, pdf_generator, sample_project_data
    ):
        """Test generowania PDF z pełnymi personami."""
        pdf_bytes = await pdf_generator.generate_project_pdf(
            project_data=sample_project_data,
            user_tier="pro",
            include_full_personas=True,
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    @pytest.mark.asyncio
    async def test_generate_project_pdf_empty_project(self, pdf_generator):
        """Test generowania PDF dla projektu bez danych."""
        empty_project = {
            "id": "empty-id",
            "name": "Pusty Projekt",
            "description": "",
            "personas": [],
            "focus_groups": [],
            "surveys": [],
        }

        pdf_bytes = await pdf_generator.generate_project_pdf(
            project_data=empty_project,
            user_tier="free",
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # Nawet pusty projekt powinien mieć podstawową strukturę
        assert b"%PDF" in pdf_bytes

    def test_aggregate_demographics(self, pdf_generator):
        """Test agregacji statystyk demograficznych."""
        personas = [
            {"age": 25, "gender": "male", "education_level": "Bachelor's", "location": "Warsaw"},
            {"age": 30, "gender": "female", "education_level": "Master's", "location": "Warsaw"},
            {"age": 28, "gender": "male", "education_level": "Bachelor's", "location": "Krakow"},
        ]

        stats = pdf_generator._aggregate_demographics(personas)

        assert stats["total_personas"] == 3
        assert stats["age_range"] == "25-30"
        assert stats["avg_age"] == 27.7
        assert stats["gender_distribution"]["male"] == 2
        assert stats["gender_distribution"]["female"] == 1

    def test_aggregate_demographics_empty(self, pdf_generator):
        """Test agregacji dla pustej listy person."""
        stats = pdf_generator._aggregate_demographics([])
        assert stats == {}

    def test_extract_focus_group_insights(self, pdf_generator):
        """Test ekstrakcji insightów z grup fokusowych."""
        focus_groups = [
            {
                "persona_ids": ["p1", "p2"],
                "ai_summary": {"key_themes": ["Temat A", "Temat B"]},
            },
            {
                "persona_ids": ["p3"],
                "ai_summary": {"key_themes": ["Temat C"]},
            },
        ]

        insights = pdf_generator._extract_focus_group_insights(focus_groups)

        assert insights["focus_groups_count"] == 2
        assert insights["participant_count"] == 3
        assert "Temat A" in insights["key_themes"]

    def test_aggregate_survey_responses(self, pdf_generator):
        """Test agregacji odpowiedzi z ankiet."""
        surveys = [
            {"status": "completed", "actual_responses": 50},
            {"status": "completed", "actual_responses": 30},
            {"status": "draft", "actual_responses": 0},
        ]

        aggregates = pdf_generator._aggregate_survey_responses(surveys)

        assert aggregates["surveys_count"] == 3
        assert aggregates["total_responses"] == 80
        assert aggregates["completed_surveys"] == 2
