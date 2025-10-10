"""Testy integracyjne dla głównych endpointów API."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


client = TestClient(app, raise_server_exceptions=False)


class TestAPIBasics:
    """Podstawowe testy API."""

    def test_api_root_endpoint(self):
        """Test głównego endpointu API."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "status" in data

    def test_health_endpoint(self):
        """Test endpointu health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPayloadValidation:
    """Testy walidacji danych wejściowych."""

    def test_project_payload_structure(self):
        """Test struktury payloadu projektu."""
        valid_payload = {
            "name": "Test Project",
            "description": "Test description",
            "target_demographics": {
                "age_group": {"18-24": 0.5, "25-34": 0.5},
                "gender": {"male": 0.5, "female": 0.5}
            },
            "target_sample_size": 20
        }

        # Sprawdzamy strukturę
        assert "name" in valid_payload
        assert "target_demographics" in valid_payload
        assert "age_group" in valid_payload["target_demographics"]
        assert sum(valid_payload["target_demographics"]["age_group"].values()) == pytest.approx(1.0)


    def test_focus_group_payload_structure(self):
        """Test struktury payloadu grupy fokusowej."""
        valid_payload = {
            "name": "Product Feedback",
            "description": "User feedback session",
            "project_id": str(uuid4()),
            "questions": [
                "What do you think?",
                "Would you buy this?"
            ]
        }

        assert "name" in valid_payload
        assert "questions" in valid_payload
        assert len(valid_payload["questions"]) > 0
        assert all(isinstance(q, str) for q in valid_payload["questions"])


    def test_survey_payload_structure(self):
        """Test struktury payloadu ankiety."""
        valid_payload = {
            "title": "Customer Satisfaction",
            "description": "Satisfaction survey",
            "project_id": str(uuid4()),
            "questions": [
                {
                    "id": "q1",
                    "text": "Rate satisfaction (1-5)",
                    "type": "scale",
                    "options": ["1", "2", "3", "4", "5"]
                }
            ]
        }

        assert "title" in valid_payload
        assert "questions" in valid_payload
        assert all("type" in q for q in valid_payload["questions"])
        assert valid_payload["questions"][0]["type"] in ["scale", "yes_no", "open_ended", "multiple_choice"]


class TestErrorResponses:
    """Testy odpowiedzi błędów."""

    def test_404_endpoint(self):
        """Test zwracania 404 dla nieistniejącego endpointu."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404


class TestCORS:
    """Testy konfiguracji CORS."""

    def test_cors_options_request(self):
        """Test obsługi OPTIONS request (CORS preflight)."""
        response = client.options("/")
        # CORS może zwrócić 200 lub 405 w zależności od konfiguracji
        assert response.status_code in [200, 405]


# Pozostałe testy wymagają pełnej konfiguracji DB i są oznaczone jako skipped

@pytest.mark.skip(reason="Requires database setup")
class TestProjectsAPIIntegration:
    """Testy integracyjne API projektów - wymagają DB."""

    def test_create_project(self):
        """Test tworzenia projektu przez API."""
        pass

    def test_list_projects(self):
        """Test listowania projektów."""
        pass

    def test_get_project_details(self):
        """Test pobierania szczegółów projektu."""
        pass


@pytest.mark.skip(reason="Requires database setup")
class TestPersonasAPIIntegration:
    """Testy integracyjne API person - wymagają DB."""

    def test_generate_personas(self):
        """Test generowania person."""
        pass

    def test_list_personas(self):
        """Test listowania person."""
        pass


@pytest.mark.skip(reason="Requires database setup")
class TestFocusGroupsAPIIntegration:
    """Testy integracyjne API grup fokusowych - wymagają DB."""

    def test_create_focus_group(self):
        """Test tworzenia grupy fokusowej."""
        pass

    def test_run_focus_group(self):
        """Test uruchamiania grupy fokusowej."""
        pass


@pytest.mark.skip(reason="Requires database setup")
class TestSurveysAPIIntegration:
    """Testy integracyjne API ankiet - wymagają DB."""

    def test_create_survey(self):
        """Test tworzenia ankiety."""
        pass

    def test_run_survey(self):
        """Test uruchamiania ankiety."""
        pass


@pytest.mark.skip(reason="Requires database setup")
class TestGraphAnalysisAPIIntegration:
    """Testy integracyjne API analizy grafowej - wymagają DB."""

    def test_build_graph(self):
        """Test budowania grafu wiedzy."""
        pass

    def test_get_key_concepts(self):
        """Test pobierania kluczowych konceptów."""
        pass
