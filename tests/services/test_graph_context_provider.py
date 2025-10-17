"""
Testy dla GraphContextProvider

Test suite:
- test_get_segment_nodes_success - pomyślny fetch nodes
- test_get_segment_nodes_cache_hit - cache hit scenario
- test_get_segment_nodes_graceful_degradation - error handling
- test_get_top_insights_sorting - sorting by confidence
- test_get_top_insights_empty_nodes - empty input handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.rag.graph_context_provider import GraphContextProvider
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
def sample_graph_nodes():
    """Fixture: sample graph nodes dla testów."""
    return [
        {
            "type": "Trend",
            "summary": "Wzrost zapotrzebowania na usługi IT w Warszawie",
            "confidence": "high",
            "magnitude": "Wysoka",
            "source": "Raport GUS 2023"
        },
        {
            "type": "Insight",
            "summary": "Kobiety 30-40 lat dominują w sektorze IT",
            "confidence": "medium",
            "source": "LinkedIn Report"
        },
        {
            "type": "Observation",
            "summary": "Średnie zarobki specjalistów IT: 10k zł",
            "confidence": "low",
            "source": "Salary Survey"
        }
    ]


@pytest.mark.asyncio
async def test_get_segment_nodes_success(sample_persona, sample_graph_nodes):
    """Test pomyślnego fetch graph nodes."""
    provider = GraphContextProvider()

    # Mock GraphRAGService response
    with patch.object(
        provider.graph_rag,
        'get_demographic_graph_context',
        autospec=True
    ) as mock_graph_rag:
        mock_graph_rag.return_value = sample_graph_nodes

        # Execute
        nodes = await provider.get_segment_nodes(sample_persona, limit=10)

        # Verify
        assert len(nodes) == 3
        assert nodes[0]["type"] == "Trend"
        assert nodes[0]["confidence"] == "high"

        # Verify GraphRAG called with correct filter
        call_args = mock_graph_rag.call_args
        # call_args.args[0] == self
        assert call_args.args[1] == "35-44"
        assert call_args.args[2] == "Warszawa"
        assert call_args.args[3] == "Wyższe magisterskie"
        assert call_args.args[4] == "kobieta"


@pytest.mark.asyncio
async def test_get_segment_nodes_cache_hit(sample_persona, sample_graph_nodes):
    """Test cache hit scenario dla graph nodes."""
    provider = GraphContextProvider()

    # Mock Redis cache (cache hit)
    with patch('app.services.rag.graph_context_provider.redis_get_json', new_callable=AsyncMock) as mock_redis_get:
        mock_redis_get.return_value = sample_graph_nodes

        # Execute
        nodes = await provider.get_segment_nodes(sample_persona, limit=10)

        # Verify
        assert len(nodes) == 3
        assert nodes[0]["type"] == "Trend"

        # Verify Redis was queried
        assert mock_redis_get.called


@pytest.mark.asyncio
async def test_get_segment_nodes_graceful_degradation(sample_persona):
    """Test graceful degradation when GraphRAG fails."""
    provider = GraphContextProvider()

    # Mock GraphRAGService to raise exception
    with patch.object(
        provider.graph_rag,
        'get_demographic_graph_context',
        new_callable=MagicMock
    ) as mock_graph_rag:
        mock_graph_rag.side_effect = Exception("GraphRAG service unavailable")

        # Execute
        nodes = await provider.get_segment_nodes(sample_persona, limit=10)

        # Verify graceful degradation
        assert nodes == []  # Empty list, nie exception


@pytest.mark.asyncio
async def test_get_top_insights_sorting(sample_persona, sample_graph_nodes):
    """Test sorting insights by confidence."""
    provider = GraphContextProvider()

    # Mock get_segment_nodes to return unsorted nodes
    with patch.object(
        provider,
        'get_segment_nodes',
        new_callable=AsyncMock
    ) as mock_get_nodes:
        mock_get_nodes.return_value = sample_graph_nodes  # Low -> Med -> High (unsorted)

        # Execute
        insights = await provider.get_top_insights(sample_persona, limit=5)

        # Verify sorting (high first, then medium, then low)
        assert insights[0]["confidence"] == "high"
        assert insights[1]["confidence"] == "medium"
        assert insights[2]["confidence"] == "low"


@pytest.mark.asyncio
async def test_get_top_insights_empty_nodes(sample_persona):
    """Test get_top_insights z pustą listą nodes."""
    provider = GraphContextProvider()

    # Mock get_segment_nodes to return empty list
    with patch.object(
        provider,
        'get_segment_nodes',
        new_callable=AsyncMock
    ) as mock_get_nodes:
        mock_get_nodes.return_value = []

        # Execute
        insights = await provider.get_top_insights(sample_persona, limit=5)

        # Verify
        assert insights == []
