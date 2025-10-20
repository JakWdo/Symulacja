"""Testy dla endpointów analitycznych (AI summaries i transkrypcje)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import analysis
from app.services.focus_groups.discussion_summarizer import DiscussionSummarizerService


client = TestClient(app, raise_server_exceptions=False)


@dataclass
class StubFocusGroup:
    """Minimalna reprezentacja grupy fokusowej używana w testach."""

    id: UUID
    questions: List[str] = field(default_factory=list)
    ai_summary: Dict[str, Any] | None = None


@dataclass
class StubPersonaResponse:
    """Uproszczona odpowiedź persony na potrzeby testów API."""

    persona_id: UUID
    focus_group_id: UUID
    question_text: str
    response_text: str
    response_time_ms: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class _ScalarResultStub:
    """Imituje wynik metody `scalars()` SQLAlchemy."""

    def __init__(self, items: Iterable[Any]):
        self._items = list(items)

    def all(self) -> List[Any]:
        return list(self._items)


class _ExecuteResultStub:
    """Imituje wynik zwracany przez `AsyncSession.execute`."""

    def __init__(self, items: Iterable[Any]):
        self._items = list(items)

    def scalars(self) -> _ScalarResultStub:
        return _ScalarResultStub(self._items)


class FakeAsyncSession:
    """Minimalna implementacja AsyncSession na potrzeby testów."""

    def __init__(self, response_source: "TestDataStore") -> None:
        self._response_source = response_source
        self.commit_calls = 0
        self.rollback_calls = 0

    async def execute(self, statement: Any) -> _ExecuteResultStub:  # pragma: no cover - SQL ignorujemy
        focus_group_id = getattr(self._response_source, "current_focus_group_id", None)
        responses = [
            response
            for response in self._response_source.responses
            if focus_group_id is None or response.focus_group_id == focus_group_id
        ]
        return _ExecuteResultStub(responses)

    async def commit(self) -> None:
        self.commit_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1


@dataclass
class TestDataStore:
    """Przechowuje dane wykorzystywane przez stuby w trakcie testów."""

    focus_groups: Dict[UUID, StubFocusGroup] = field(default_factory=dict)
    responses: List[StubPersonaResponse] = field(default_factory=list)
    current_focus_group_id: UUID | None = None


@pytest.fixture
def analysis_test_context(monkeypatch: pytest.MonkeyPatch):
    """Konfiguruje środowisko testowe z asynchronicznymi stubami zależności."""

    store = TestDataStore()
    fake_db = FakeAsyncSession(store)
    fake_user = SimpleNamespace(id=uuid4(), email="tester@example.com")

    async def get_db_stub() -> FakeAsyncSession:
        return fake_db

    async def get_current_user_stub() -> SimpleNamespace:
        return fake_user

    async def get_focus_group_stub(
        db: FakeAsyncSession, focus_group_id: UUID, current_user: SimpleNamespace
    ) -> StubFocusGroup:
        store.current_focus_group_id = focus_group_id
        try:
            return store.focus_groups[focus_group_id]
        except KeyError as exc:  # pragma: no cover - obsługa braku grupy
            raise ValueError("Focus group not found") from exc

    original_focus_group_getter = analysis._get_focus_group
    monkeypatch.setattr(analysis, "_get_focus_group", get_focus_group_stub)

    app.dependency_overrides[analysis.get_db] = get_db_stub
    app.dependency_overrides[analysis.get_current_user] = get_current_user_stub

    try:
        yield store, fake_db
    finally:
        analysis._get_focus_group = original_focus_group_getter
        app.dependency_overrides.pop(analysis.get_db, None)
        app.dependency_overrides.pop(analysis.get_current_user, None)


def test_generate_insights_returns_summary(monkeypatch: pytest.MonkeyPatch, analysis_test_context):
    store, fake_db = analysis_test_context
    focus_group_id = uuid4()
    store.focus_groups[focus_group_id] = StubFocusGroup(id=focus_group_id, questions=["Q1"])

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "__init__",
        lambda self, use_pro_model=False: None,
    )

    sample_summary = {
        "executive_summary": "Summary",
        "insights": ["Insight 1"],
    }

    async def summary_stub(self, **kwargs: Any) -> Dict[str, Any]:
        return sample_summary

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "generate_discussion_summary",
        summary_stub,
    )

    response = client.post(f"/api/v1/focus-groups/{focus_group_id}/insights")

    assert response.status_code == 200
    assert response.json() == sample_summary
    assert fake_db.commit_calls == 1
    assert fake_db.rollback_calls == 0


def test_generate_insights_handles_not_found(monkeypatch: pytest.MonkeyPatch, analysis_test_context):
    store, fake_db = analysis_test_context
    focus_group_id = uuid4()
    store.focus_groups[focus_group_id] = StubFocusGroup(id=focus_group_id)

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "__init__",
        lambda self, use_pro_model=False: None,
    )

    async def summary_stub(self, **kwargs: Any) -> Dict[str, Any]:
        raise ValueError("missing focus group data")

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "generate_discussion_summary",
        summary_stub,
    )

    response = client.post(f"/api/v1/focus-groups/{focus_group_id}/insights")

    assert response.status_code == 404
    assert response.json()["detail"] == "missing focus group data"
    assert fake_db.commit_calls == 0
    assert fake_db.rollback_calls == 1


def test_generate_insights_handles_server_error(monkeypatch: pytest.MonkeyPatch, analysis_test_context):
    store, fake_db = analysis_test_context
    focus_group_id = uuid4()
    store.focus_groups[focus_group_id] = StubFocusGroup(id=focus_group_id)

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "__init__",
        lambda self, use_pro_model=False: None,
    )

    async def summary_stub(self, **kwargs: Any) -> Dict[str, Any]:
        raise RuntimeError("unexpected error")

    monkeypatch.setattr(
        DiscussionSummarizerService,
        "generate_discussion_summary",
        summary_stub,
    )

    response = client.post(f"/api/v1/focus-groups/{focus_group_id}/insights")

    assert response.status_code == 500
    assert "unexpected error" in response.json()["detail"]
    assert fake_db.commit_calls == 0
    assert fake_db.rollback_calls == 1


def test_get_insights_returns_cached_summary(analysis_test_context):
    store, _ = analysis_test_context
    focus_group_id = uuid4()
    cached_summary = {"executive_summary": "Cached", "insights": []}
    store.focus_groups[focus_group_id] = StubFocusGroup(
        id=focus_group_id,
        questions=["Q1"],
        ai_summary=cached_summary,
    )

    response = client.get(f"/api/v1/focus-groups/{focus_group_id}/insights")

    assert response.status_code == 200
    assert response.json() == cached_summary


def test_get_insights_missing_summary_returns_404(analysis_test_context):
    store, _ = analysis_test_context
    focus_group_id = uuid4()
    store.focus_groups[focus_group_id] = StubFocusGroup(id=focus_group_id, questions=["Q1"], ai_summary=None)

    response = client.get(f"/api/v1/focus-groups/{focus_group_id}/insights")

    assert response.status_code == 404
    assert "Insights not found" in response.json()["detail"]


def test_get_focus_group_responses_returns_grouped_data(analysis_test_context):
    store, _ = analysis_test_context
    focus_group_id = uuid4()
    other_focus_group_id = uuid4()

    store.focus_groups[focus_group_id] = StubFocusGroup(
        id=focus_group_id,
        questions=["Question A", "Question B"],
    )
    store.focus_groups[other_focus_group_id] = StubFocusGroup(
        id=other_focus_group_id,
        questions=["Other"],
    )

    store.responses = [
        StubPersonaResponse(
            persona_id=uuid4(),
            focus_group_id=focus_group_id,
            question_text="Question A",
            response_text="Answer 1",
            response_time_ms=2000,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ),
        StubPersonaResponse(
            persona_id=uuid4(),
            focus_group_id=focus_group_id,
            question_text="Question C",
            response_text="Answer 2",
            response_time_ms=2500,
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        ),
        StubPersonaResponse(
            persona_id=uuid4(),
            focus_group_id=other_focus_group_id,
            question_text="Other",
            response_text="Ignore me",
            response_time_ms=3000,
            created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        ),
    ]

    response = client.get(f"/api/v1/focus-groups/{focus_group_id}/responses")

    assert response.status_code == 200
    payload = response.json()
    assert payload["focus_group_id"] == str(focus_group_id)
    assert payload["total_responses"] == 2

    grouped = {entry["question"]: entry["responses"] for entry in payload["questions"]}
    assert len(grouped["Question A"]) == 1
    assert grouped["Question A"][0]["response"] == "Answer 1"
    assert grouped["Question C"][0]["response"] == "Answer 2"

