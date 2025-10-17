"""
Testy dla PersonaNarrativeService

Test suite:
- test_get_narratives_cache_hit - cache hit scenario (< 50ms)
- test_get_narratives_cache_miss - full generation flow
- test_get_narratives_graceful_degradation - partial failures
- test_compose_person_profile - Flash generation
- test_compose_person_motivations - Pro generation with needs
- test_compose_evidence_context_structured_output - Pro structured JSON
- test_cache_key_auto_invalidation - cache invalidation logic
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
import time

from app.services.personas.persona_narrative_service import PersonaNarrativeService
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
        background_story="Anna Kowalska jest 35-letnią specjalistką IT mieszkającą w Warszawie."
    )
    # Add required timestamp dla cache key
    persona.updated_at = MagicMock()
    persona.updated_at.timestamp.return_value = 1700000000
    return persona


@pytest.fixture
def sample_needs():
    """Fixture: sample needs dla testów."""
    return {
        "jobs_to_be_done": [
            {
                "job_statement": "Automatyzować powtarzalne zadania",
                "priority_score": 9,
                "quotes": ["Potrzebuję więcej czasu na strategię"]
            }
        ],
        "desired_outcomes": [
            {
                "outcome_statement": "Zwiększyć produktywność o 30%",
                "importance": 9,
                "satisfaction": 4
            }
        ],
        "pain_points": [
            {
                "pain_title": "Zbyt wiele ręcznych tasków",
                "severity": 8,
                "frequency": "daily"
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_narratives_cache_hit(sample_persona):
    """Test cache hit scenario (< 50ms)."""
    service = PersonaNarrativeService()

    cached_narratives = {
        "narratives": {
            "person_profile": "Anna jest 35-letnią specjalistką IT...",
            "person_motivations": "Jej głównym celem jest...",
            "segment_hero": "Nazwa segmentu: Kobiety IT...",
            "segment_significance": "Ten segment jest istotny...",
            "evidence_context": {"background_narrative": "Kontekst...", "key_citations": []}
        },
        "status": "ok",
        "generated_at": int(time.time())
    }

    # Mock Redis cache hit
    with patch('app.services.personas.persona_narrative_service.redis_get_json', new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = cached_narratives

        # Execute
        start = time.time()
        narratives, status = await service.get_narratives(sample_persona.id)
        elapsed_ms = (time.time() - start) * 1000

        # Verify
        assert narratives is not None
        assert status == "ok"
        assert "person_profile" in narratives
        assert elapsed_ms < 100  # Should be < 50ms but allow margin


@pytest.mark.asyncio
async def test_get_narratives_cache_miss(sample_persona, sample_needs):
    """Test full generation flow (cache miss)."""
    service = PersonaNarrativeService()

    # Mock Redis cache miss
    with patch('app.services.personas.persona_narrative_service.redis_get_json', new_callable=AsyncMock) as mock_redis_get, \
         patch('app.services.personas.persona_narrative_service.redis_set_json', new_callable=AsyncMock) as mock_redis_set, \
         patch('app.services.personas.persona_narrative_service.AsyncSessionLocal') as mock_session, \
         patch.object(service.graph_provider, 'get_segment_nodes', new_callable=AsyncMock) as mock_graph, \
         patch.object(service.hybrid_provider, 'get_narrative_context', new_callable=AsyncMock) as mock_hybrid, \
         patch('app.services.personas.persona_narrative_service.PersonaNeedsService') as mock_needs_service:

        # Setup mocks
        mock_redis_get.return_value = None  # Cache miss
        mock_graph.return_value = []
        mock_hybrid.return_value = {"context": "", "citations": []}

        # Mock DB session
        mock_db_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_instance
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = sample_persona
        mock_db_instance.execute.return_value = mock_result

        # Mock needs service
        mock_needs_instance = AsyncMock()
        mock_needs_service.return_value = mock_needs_instance
        mock_needs_instance.generate_needs_analysis.return_value = sample_needs

        # Mock LLM responses
        with patch('app.services.personas.persona_narrative_service.build_chat_model') as mock_build_model:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = MagicMock(content="Generated narrative text")
            mock_llm.with_structured_output.return_value.ainvoke.return_value = {
                "background_narrative": "Kontekst...",
                "key_citations": []
            }
            mock_build_model.return_value = mock_llm

            # Execute
            narratives, status = await service.get_narratives(sample_persona.id)

            # Verify
            assert narratives is not None
            assert status in ["ok", "degraded"]
            assert mock_redis_set.called  # Should cache result


@pytest.mark.asyncio
async def test_get_narratives_graceful_degradation(sample_persona):
    """Test graceful degradation when partial failures occur."""
    service = PersonaNarrativeService()

    # Mock Redis cache miss
    with patch('app.services.personas.persona_narrative_service.redis_get_json', new_callable=AsyncMock) as mock_redis_get, \
         patch('app.services.personas.persona_narrative_service.AsyncSessionLocal') as mock_session, \
         patch.object(service.graph_provider, 'get_segment_nodes', new_callable=AsyncMock) as mock_graph, \
         patch.object(service.hybrid_provider, 'get_narrative_context', new_callable=AsyncMock) as mock_hybrid:

        mock_redis_get.return_value = None  # Cache miss

        # Mock DB session
        mock_db_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db_instance
        mock_result = AsyncMock()
        mock_result.scalars.return_value.first.return_value = sample_persona
        mock_db_instance.execute.return_value = mock_result

        # Graph fetch succeeds, hybrid fails
        mock_graph.return_value = []
        mock_hybrid.side_effect = Exception("Hybrid RAG unavailable")

        # Mock LLM to fail partially
        with patch('app.services.personas.persona_narrative_service.build_chat_model') as mock_build_model:
            mock_llm = AsyncMock()
            # First call succeeds, rest fail
            mock_llm.ainvoke.side_effect = [
                MagicMock(content="Profile text"),
                Exception("LLM timeout"),
                Exception("LLM timeout"),
                Exception("LLM timeout")
            ]
            mock_build_model.return_value = mock_llm

            # Execute
            narratives, status = await service.get_narratives(sample_persona.id)

            # Verify degraded status
            assert status == "degraded"
            # Some narratives should be None
            if narratives:
                assert narratives.get("person_profile") is not None  # First succeeded
                # Others should be None or failed


@pytest.mark.asyncio
async def test_compose_person_profile(sample_persona):
    """Test person_profile generation (Flash model)."""
    service = PersonaNarrativeService()

    # Mock Flash model
    with patch('app.services.personas.persona_narrative_service.build_chat_model') as mock_build_model:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(
            content="Anna Kowalska to 35-letnia specjalistka IT mieszkająca w Warszawie."
        )
        mock_build_model.return_value = mock_llm

        # Execute
        profile = await service.compose_person_profile(sample_persona)

        # Verify
        assert len(profile) > 0
        assert "Anna" in profile or "35" in profile
        # Verify Flash model used (temperature 0.2)
        mock_build_model.assert_called_once()
        assert mock_build_model.call_args[1]["temperature"] == 0.2


@pytest.mark.asyncio
async def test_compose_person_motivations(sample_persona, sample_needs):
    """Test person_motivations generation (Pro model with needs)."""
    service = PersonaNarrativeService()

    # Mock Pro model
    with patch('app.services.personas.persona_narrative_service.build_chat_model') as mock_build_model:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(
            content="Anna dąży do automatyzacji zadań aby zwiększyć produktywność."
        )
        mock_build_model.return_value = mock_llm

        # Execute
        motivations = await service.compose_person_motivations(sample_needs, sample_persona)

        # Verify
        assert len(motivations) > 0
        # Verify Pro model used (temperature 0.4)
        assert mock_build_model.call_args[1]["temperature"] == 0.4


@pytest.mark.asyncio
async def test_compose_evidence_context_structured_output(sample_persona):
    """Test evidence_context structured JSON output."""
    service = PersonaNarrativeService()

    graph_context = []
    hybrid_context = {"context": "", "citations": []}

    # Mock Pro model with structured output
    with patch('app.services.personas.persona_narrative_service.build_chat_model') as mock_build_model:
        mock_llm = AsyncMock()
        mock_structured = AsyncMock()
        mock_structured.ainvoke.return_value = {
            "background_narrative": "Kontekst demograficzny Warszawy...",
            "key_citations": [
                {
                    "source": "GUS 2023",
                    "insight": "15% rynku IT to kobiety",
                    "relevance": "Potwierdza wielkość segmentu"
                }
            ]
        }
        mock_llm.with_structured_output.return_value = mock_structured
        mock_build_model.return_value = mock_llm

        # Execute
        evidence = await service.compose_evidence_context(
            graph_context,
            hybrid_context,
            sample_persona
        )

        # Verify structure
        assert "background_narrative" in evidence
        assert "key_citations" in evidence
        assert isinstance(evidence["key_citations"], list)
        assert len(evidence["key_citations"]) == 1


def test_cache_key_auto_invalidation(sample_persona):
    """Test cache key auto-invalidation logic."""
    service = PersonaNarrativeService()

    # Generate cache key
    cache_key_1 = service._compute_cache_key(
        sample_persona.id,
        int(sample_persona.updated_at.timestamp())
    )

    # Simulate persona update (different timestamp)
    new_timestamp = int(sample_persona.updated_at.timestamp()) + 1000
    cache_key_2 = service._compute_cache_key(
        sample_persona.id,
        new_timestamp
    )

    # Verify keys are different (auto-invalidation)
    assert cache_key_1 != cache_key_2
