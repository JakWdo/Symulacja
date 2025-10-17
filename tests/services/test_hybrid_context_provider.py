"""
Testy dla HybridContextProvider

Test suite:
- test_get_narrative_context_success - pomyślny fetch context
- test_get_narrative_context_cache_hit - cache hit scenario
- test_get_narrative_context_graceful_degradation - error handling
- test_demographic_query_formatting - query formatting logic
- test_citations_normalization - citations structure normalization
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.rag.hybrid_context_provider import HybridContextProvider
from app.models import Persona


@pytest.fixture
def sample_persona():
    """Fixture: sample persona dla testów."""
    persona = Persona(
        id=uuid4(),
        project_id=uuid4(),
        age=35,
        gender="Kobieta",
        location="Warszawa",
        education_level="Wyższe magisterskie",
        income_bracket="7 500 - 10 000 zł",
        occupation="Specjalista IT",
        background_story="Sample background"
    )
    return persona


@pytest.fixture
def sample_rag_insights():
    """Fixture: sample RAG insights dla testów."""
    return {
        "context": "Kobiety 30-40 lat w Warszawie z wyższym wykształceniem stanowią 15% rynku IT.",
        "citations": [
            {
                "document_title": "Raport GUS 2023",
                "chunk_text": "15% rynku IT to kobiety 30-40 lat...",
                "relevance_score": 0.89
            },
            {
                "document_title": "LinkedIn Trends",
                "chunk_text": "Wzrost zatrudnienia kobiet w IT...",
                "relevance_score": 0.76
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_narrative_context_success(sample_persona, sample_rag_insights):
    """Test pomyślnego fetch narrative context."""
    provider = HybridContextProvider()

    # Mock PolishSocietyRAG response
    with patch.object(
        provider.hybrid_rag,
        'get_demographic_insights',
        new_callable=AsyncMock
    ) as mock_hybrid_rag:
        mock_hybrid_rag.return_value = sample_rag_insights

        # Execute
        context = await provider.get_narrative_context(sample_persona, top_k=5)

        # Verify
        assert "context" in context
        assert "citations" in context
        assert len(context["context"]) > 0
        assert len(context["citations"]) == 2
        assert context["citations"][0]["relevance_score"] == 0.89

        # Verify hybrid RAG called
        call_kwargs = mock_hybrid_rag.call_args.kwargs
        assert call_kwargs["age_group"] == "35-44"
        assert call_kwargs["education"] == "Wyższe magisterskie"
        assert call_kwargs["location"] == "Warszawa"
        assert call_kwargs["gender"] == "kobieta"
        assert context["metadata"]["query"].startswith("Kobiety, wiek 35-44")


@pytest.mark.asyncio
async def test_get_narrative_context_cache_hit(sample_persona, sample_rag_insights):
    """Test cache hit scenario dla narrative context."""
    provider = HybridContextProvider()

    # Mock Redis cache (cache hit)
    with patch('app.services.rag.hybrid_context_provider.redis_get_json', new_callable=AsyncMock) as mock_redis_get:
        mock_redis_get.return_value = sample_rag_insights

        # Execute
        context = await provider.get_narrative_context(sample_persona, top_k=5)

        # Verify
        assert context["context"] == sample_rag_insights["context"]
        assert len(context["citations"]) == 2

        # Verify Redis was queried
        assert mock_redis_get.called


@pytest.mark.asyncio
async def test_get_narrative_context_graceful_degradation(sample_persona):
    """Test graceful degradation when Hybrid RAG fails."""
    provider = HybridContextProvider()

    # Mock PolishSocietyRAG to raise exception
    with patch.object(
        provider.hybrid_rag,
        'get_demographic_insights',
        new_callable=AsyncMock
    ) as mock_hybrid_rag:
        mock_hybrid_rag.side_effect = Exception("Hybrid RAG service unavailable")

        # Execute
        context = await provider.get_narrative_context(sample_persona, top_k=5)

        # Verify graceful degradation
        assert context["context"] == ""
        assert context["citations"] == []
        assert "error" in context["metadata"]


@pytest.mark.asyncio
async def test_demographic_query_formatting(sample_persona):
    """Test demographic query formatting logic."""
    provider = HybridContextProvider()

    # Mock hybrid RAG
    with patch.object(
        provider.hybrid_rag,
        'get_demographic_insights',
        new_callable=AsyncMock
    ) as mock_hybrid_rag:
        mock_hybrid_rag.return_value = {"context": "", "citations": []}

        # Execute
        result = await provider.get_narrative_context(sample_persona, top_k=5)

        # Verify query format and metadata
        call_kwargs = mock_hybrid_rag.call_args.kwargs
        assert call_kwargs["age_group"] == "35-44"
        assert call_kwargs["education"] == "Wyższe magisterskie"
        assert call_kwargs["location"] == "Warszawa"
        assert call_kwargs["gender"] == "kobieta"

        metadata = result["metadata"]
        assert metadata["query"].startswith("Kobiety, wiek 35-44")
        assert metadata["age_group"] == "35-44"
        assert metadata["gender"] == "kobieta"
        assert metadata["location"] == "Warszawa"
        assert metadata["education"] == "Wyższe magisterskie"


@pytest.mark.asyncio
async def test_citations_normalization():
    """Test citations structure normalization."""
    provider = HybridContextProvider()
    persona = Persona(
        id=uuid4(),
        project_id=uuid4(),
        age=30,
        gender="Mężczyzna"
    )

    # Mock hybrid RAG with old citation format (backward compatibility)
    with patch.object(
        provider.hybrid_rag,
        'get_demographic_insights',
        new_callable=AsyncMock
    ) as mock_hybrid_rag:
        mock_hybrid_rag.return_value = {
            "context": "Sample",
            "citations": [
                {
                    "text": "Old format citation",  # Old field name
                    "score": 0.8,  # Old field name
                    "metadata": {"title": "Old Doc"}
                }
            ]
        }

        # Execute
        context = await provider.get_narrative_context(persona, top_k=5)

        # Verify normalization
        assert len(context["citations"]) == 1
        assert context["citations"][0]["chunk_text"] == "Old format citation"
        assert context["citations"][0]["relevance_score"] == 0.8
        assert context["citations"][0]["document_title"] == "Old Doc"
