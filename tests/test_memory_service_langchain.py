"""Testy funkcji pomocniczych MemoryServiceLangChain."""

import pytest

from app.services.memory_service_langchain import MemoryServiceLangChain


class DummyEmbeddings:
    """Prosty obiekt zastępujący serwis embeddingów."""

    async def aembed_query(self, text: str):  # pragma: no cover - prosty stub
        return [float(len(text)), 1.0]


def _make_service() -> MemoryServiceLangChain:
    """Tworzy instancję serwisu bez wywoływania kosztownego __init__."""
    service = MemoryServiceLangChain.__new__(MemoryServiceLangChain)
    service.embeddings = DummyEmbeddings()
    return service


@pytest.mark.asyncio
async def test_generate_embedding_uses_stub():
    """Sprawdza czy _generate_embedding korzysta z obiektu embeddings."""
    service = _make_service()
    vector = await service._generate_embedding("abc")
    assert vector == [3.0, 1.0]


def test_event_to_text_formats_types():
    """Konwersja eventów na tekst powinna zależeć od typu."""
    service = _make_service()
    response_text = service._event_to_text(
        "response_given", {"question": "Q?", "response": "A!"}
    )
    question_text = service._event_to_text("question_asked", {"question": "Q?"})
    other_text = service._event_to_text("other", {"value": 1})

    assert "Response" in response_text
    assert response_text.startswith("Question: Q?")
    assert question_text == "Question: Q?"
    assert other_text == "{'value': 1}"


def test_format_context_creates_readable_output():
    """Formatowanie kontekstu powinno zawierać indeksy i dane eventu."""
    service = _make_service()
    context = [
        {
            "event_type": "response_given",
            "event_data": {"question": "Q?", "response": "A!"},
            "timestamp": "2024-01-01T00:00:00",
        }
    ]

    formatted = service._format_context(context)

    assert "1." in formatted
    assert "Q?" in formatted
    assert "A!" in formatted


def test_cosine_similarity_known_values():
    """Cosinus znanych wektorów powinien zwracać oczekiwane wartości."""
    service = _make_service()
    assert service._cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert service._cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0, abs=1e-6)
