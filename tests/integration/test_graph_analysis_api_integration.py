"""Integration-style tests for graph analysis endpoints with service stubs."""

from __future__ import annotations

from typing import Any, Dict

import pytest

class _GraphServiceStub:
    """In-memory stub that mimics GraphService behaviour for API contract tests."""

    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True

    async def build_graph_from_focus_group(self, db, focus_group_id: str) -> Dict[str, Any]:
        return {
            "personas_added": 3,
            "concepts_extracted": 5,
            "relationships_created": 7,
            "emotions_created": 4,
        }

    async def get_graph_data(self, focus_group_id: str, filter_type: str | None, db) -> Dict[str, Any]:
        return {
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
        }

    async def get_key_concepts(self, focus_group_id: str, db):
        return [
            {"name": "Innovation", "frequency": 4, "sentiment": 0.4, "personas": ["Alice"]},
            {"name": "Pricing", "frequency": 2, "sentiment": -0.1, "personas": ["Bob"]},
        ]

    async def get_influential_personas(self, focus_group_id: str, db):
        return [
            {"id": "persona-1", "name": "Alice", "connections": 10, "sentiment": 0.6, "influence": 92},
            {"id": "persona-2", "name": "Bob", "connections": 8, "sentiment": 0.4, "influence": 80},
        ]

    async def answer_question(self, focus_group_id: str, question: str, db):
        return {
            "answer": "Innovation drives engagement among younger personas.",
            "insights": [
                {
                    "title": "High resonance",
                    "detail": "Younger personas mention innovation frequently.",
                    "metadata": {"count": 5},
                }
            ],
            "suggested_questions": ["How do older personas perceive innovation?"],
        }


@pytest.fixture
def graph_service_stub_factory(monkeypatch):
    """Patch GraphService in the API module with a deterministic stub."""
    from app.api import graph_analysis as graph_analysis_module

    class _Factory:
        def __init__(self):
            self.instances: list[_GraphServiceStub] = []

        def __call__(self):
            instance = _GraphServiceStub()
            self.instances.append(instance)
            return instance

    factory = _Factory()
    monkeypatch.setattr(graph_analysis_module, "GraphService", factory)
    return factory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_build_graph_returns_stats(completed_focus_group, graph_service_stub_factory):
    focus_group, _, client, headers = await completed_focus_group

    response = client.post(f"/api/v1/graph/build/{focus_group.id}", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["personas_added"] == 3
    assert graph_service_stub_factory.instances[-1].closed, "GraphService.close() should be awaited"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_graph_returns_nodes(completed_focus_group, graph_service_stub_factory):
    focus_group, _, client, headers = await completed_focus_group

    response = client.get(f"/api/v1/graph/{focus_group.id}", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload["nodes"]) == 2
    assert payload["links"][0]["type"] == "mentions"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_key_concepts_endpoint(completed_focus_group, graph_service_stub_factory):
    focus_group, _, client, headers = await completed_focus_group

    response = client.get(f"/api/v1/graph/{focus_group.id}/concepts", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["concepts"][0]["name"] == "Innovation"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_influential_personas_endpoint(completed_focus_group, graph_service_stub_factory):
    focus_group, _, client, headers = await completed_focus_group

    response = client.get(f"/api/v1/graph/{focus_group.id}/influential", headers=headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["personas"][0]["name"] == "Alice"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ask_graph_question_returns_answer(completed_focus_group, graph_service_stub_factory):
    focus_group, _, client, headers = await completed_focus_group

    response = client.post(
        f"/api/v1/graph/{focus_group.id}/ask",
        json={"question": "What drives engagement?"},
        headers=headers,
    )
    assert response.status_code == 200

    payload = response.json()
    assert "answer" in payload
    assert payload["insights"][0]["title"] == "High resonance"
