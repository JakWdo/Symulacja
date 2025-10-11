import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from types import SimpleNamespace
from uuid import uuid4
from copy import deepcopy

from app.main import app
from app.api import dependencies as dependencies_module
import app.api.graph_analysis as graph_analysis_module


class DummyGraphService:
    base_payloads = {
        "build_graph_from_focus_group": {
            "personas_added": 3,
            "concepts_extracted": 5,
            "relationships_created": 7,
            "emotions_created": 4,
        },
        "get_graph_data": {
            "nodes": [
                {
                    "id": "persona-1",
                    "name": "Alice",
                    "type": "persona",
                    "group": 1,
                    "size": 15,
                    "sentiment": 0.6,
                    "metadata": {"role": "Leader"},
                },
                {
                    "id": "concept-1",
                    "name": "Innovation",
                    "type": "concept",
                    "group": 2,
                    "size": 10,
                    "sentiment": 0.4,
                    "metadata": {"category": "Strategy"},
                },
            ],
            "links": [
                {
                    "source": "persona-1",
                    "target": "concept-1",
                    "type": "mentions",
                    "strength": 0.9,
                    "sentiment": 0.5,
                }
            ],
        },
        "get_influential_personas": [
            {
                "id": "persona-1",
                "name": "Alice",
                "influence": 92,
                "connections": 8,
                "sentiment": 0.6,
            }
        ],
        "get_key_concepts": [
            {
                "name": "Innovation",
                "frequency": 4,
                "sentiment": 0.4,
                "personas": ["Alice"],
            }
        ],
        "get_controversial_concepts": [
            {
                "name": "Pricing",
                "supporters": ["Alice"],
                "critics": ["Bob"],
                "sentiment_spread": 1.2,
            }
        ],
        "get_trait_opinion_correlations": [
            {
                "trait": "Age",
                "segment": "18-25",
                "concept": "Innovation",
                "difference": 0.35,
            }
        ],
        "get_emotion_distribution": [
            {
                "emotion": "Excited",
                "count": 5,
                "intensity": 0.8,
            }
        ],
        "answer_question": {
            "answer": "Innovation drives engagement among younger personas.",
            "insights": [
                {
                    "title": "High resonance",
                    "detail": "Younger personas mention innovation frequently.",
                    "metadata": {"count": 5},
                }
            ],
            "suggested_questions": [
                "How do older personas perceive innovation?"
            ],
        },
    }
    responses = {}
    instances = []

    def __init__(self):
        self.closed = False
        type(self).instances.append(self)

    @classmethod
    def reset(cls):
        cls.responses = deepcopy(cls.base_payloads)
        cls.instances = []

    async def close(self):
        self.closed = True

    async def build_graph_from_focus_group(self, db, focus_group_id):
        return await self._resolve("build_graph_from_focus_group")

    async def get_graph_data(self, focus_group_id, filter_type, db):
        return await self._resolve("get_graph_data")

    async def get_influential_personas(self, db, focus_group_id, limit=10):
        return await self._resolve("get_influential_personas")

    async def get_key_concepts(self, db, focus_group_id, limit=10):
        return await self._resolve("get_key_concepts")

    async def get_controversial_concepts(self, db, focus_group_id, limit=10):
        return await self._resolve("get_controversial_concepts")

    async def get_trait_opinion_correlations(self, db, focus_group_id, limit=10):
        return await self._resolve("get_trait_opinion_correlations")

    async def get_emotion_distribution(self, db, focus_group_id):
        return await self._resolve("get_emotion_distribution")

    async def answer_question(self, focus_group_id, question, db):
        return await self._resolve("answer_question")

    async def _resolve(self, key):
        value = self.responses[key]
        if isinstance(value, Exception):
            raise value
        return deepcopy(value)


@pytest.fixture
def graph_test_env(monkeypatch):
    DummyGraphService.reset()

    async def override_get_db():
        yield SimpleNamespace()

    async def override_get_current_user():
        return SimpleNamespace(id="user-1", is_active=True)

    async def override_get_focus_group_for_user(focus_group_id, current_user, db):
        return SimpleNamespace(id=focus_group_id, project_id="project-1", status="completed")

    app.dependency_overrides[dependencies_module.get_db] = override_get_db
    app.dependency_overrides[dependencies_module.get_current_user] = override_get_current_user

    monkeypatch.setattr(graph_analysis_module, "GraphService", DummyGraphService)
    monkeypatch.setattr(graph_analysis_module, "get_focus_group_for_user", override_get_focus_group_for_user)

    client = TestClient(app)

    yield {
        "client": client,
        "service_cls": DummyGraphService,
        "current_user_override": override_get_current_user,
    }

    client.close()
    app.dependency_overrides.clear()
    DummyGraphService.reset()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}


def test_build_graph_returns_stats_and_closes_service(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.post(f"/api/v1/graph/build/{focus_group_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == service_cls.responses["build_graph_from_focus_group"]
    assert service_cls.instances[-1].closed is True


def test_get_graph_returns_nodes_and_links(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == service_cls.responses["get_graph_data"]


def test_get_influential_personas(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}/influential", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"personas": service_cls.responses["get_influential_personas"]}


def test_get_key_concepts(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}/concepts", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"concepts": service_cls.responses["get_key_concepts"]}


def test_get_controversial_concepts(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}/controversial", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"controversial_concepts": service_cls.responses["get_controversial_concepts"]}


def test_get_trait_correlations(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}/correlations", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"correlations": service_cls.responses["get_trait_opinion_correlations"]}


def test_get_emotion_distribution(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.get(f"/api/v1/graph/{focus_group_id}/emotions", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"emotions": service_cls.responses["get_emotion_distribution"]}


def test_answer_question_returns_expected_payload(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()

    response = client.post(
        f"/api/v1/graph/{focus_group_id}/ask",
        json={"question": "What drives engagement?"},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == service_cls.responses["answer_question"]


def test_get_graph_value_error_returns_400(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()
    service_cls.responses["get_graph_data"] = ValueError("Invalid filter")

    response = client.get(f"/api/v1/graph/{focus_group_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid filter"


def test_get_graph_connection_error_returns_503(graph_test_env, auth_headers):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    focus_group_id = uuid4()
    service_cls.responses["get_graph_data"] = ConnectionError("Neo4j unavailable")

    response = client.get(f"/api/v1/graph/{focus_group_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["detail"] == "Neo4j unavailable"


def test_requests_require_authorization(graph_test_env):
    client = graph_test_env["client"]
    service_cls = graph_test_env["service_cls"]
    current_user_override = graph_test_env["current_user_override"]

    async def unauthorized_override():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    app.dependency_overrides[dependencies_module.get_current_user] = unauthorized_override

    response = client.get(f"/api/v1/graph/{uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"

    app.dependency_overrides[dependencies_module.get_current_user] = current_user_override

    response = client.get(f"/api/v1/graph/{uuid4()}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == service_cls.responses["get_graph_data"]
