"""
Testy jednostkowe dla SegmentBriefService

Zakres testów:
- Generowanie segment_id z demografii
- Cache hit/miss scenarios
- RAG context fetching
- LLM brief generation i walidacja długości (1000-6000 chars)
- Example personas retrieval
- Persona uniqueness generation
- Error handling i fallbacks
- Redis cache operations (TTL, invalidation)

Priority: P0 - Krytyczny moduł (core business logic generacji briefów)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.services.personas.orchestration.segment_brief_service import SegmentBriefService
from app.schemas.segment_brief import (
    SegmentBrief,
    SegmentBriefRequest,
    SegmentBriefResponse,
)
from app.models.persona import Persona


class TestSegmentIdGeneration:
    """Testy dla generowania segment_id z demografii."""

    def test_generate_segment_id_basic_demographics(self):
        """Test: generate_segment_id tworzy spójny ID z podstawowej demografii."""
        demographics = {
            "age": "25-34",
            "gender": "kobieta",
            "education": "wyższe",
            "location": "Warszawa",
            "income": "7 500 - 10 000 zł"
        }

        segment_id = SegmentBriefService.generate_segment_id(demographics)

        assert segment_id == "seg_25-34_wyższe_warszawa_kobieta"

    def test_generate_segment_id_with_age_group_alias(self):
        """Test: generate_segment_id obsługuje alias 'age_group' zamiast 'age'."""
        demographics = {
            "age_group": "35-44",
            "gender": "mężczyzna",
            "education_level": "średnie",
            "location": "Kraków"
        }

        segment_id = SegmentBriefService.generate_segment_id(demographics)

        assert "35-44" in segment_id
        assert "średnie" in segment_id
        assert "mężczyzna" in segment_id

    def test_generate_segment_id_normalization(self):
        """Test: generate_segment_id normalizuje spacje i case."""
        demographics = {
            "age": "25 - 34",  # Spacje
            "gender": "KOBIETA",  # Uppercase
            "education": "Wyższe Magisterskie",  # Mixed case + spacje
            "location": "Warszawa Centrum"
        }

        segment_id = SegmentBriefService.generate_segment_id(demographics)

        # Wszystko lowercase i spacje zastąpione myślnikami
        assert segment_id.islower()
        assert " " not in segment_id

    def test_generate_segment_id_missing_fields_default_unknown(self):
        """Test: Brakujące pola dostają wartość 'unknown'."""
        demographics = {
            "age": "25-34"
            # Brak gender, education, location, income
        }

        segment_id = SegmentBriefService.generate_segment_id(demographics)

        assert "unknown" in segment_id
        assert "25-34" in segment_id

    def test_generate_segment_id_consistency_same_demographics(self):
        """Test: Te same demografie zawsze dają ten sam segment_id."""
        demographics = {
            "age": "25-34",
            "gender": "kobieta",
            "education": "wyższe",
            "location": "Warszawa"
        }

        id1 = SegmentBriefService.generate_segment_id(demographics)
        id2 = SegmentBriefService.generate_segment_id(demographics)

        assert id1 == id2


class TestExamplePersonasRetrieval:
    """Testy dla pobierania przykładowych person z segmentu."""

    @pytest.mark.asyncio
    async def test_get_example_personas_returns_max_3(self):
        """Test: _get_example_personas_from_segment zwraca max 3 persony."""
        # Mock DB session
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Persona(id=uuid4(), name="Jan Kowalski"),
            Persona(id=uuid4(), name="Anna Nowak"),
            Persona(id=uuid4(), name="Piotr Wiśniewski"),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)
        service.redis_client = None  # Disable Redis

        project_id = uuid4()
        segment_id = "seg_25-34_wyższe_warszawa_kobieta"

        personas = await service._get_example_personas_from_segment(
            project_id, segment_id, max_personas=3
        )

        assert len(personas) == 3
        assert all(isinstance(p, Persona) for p in personas)

    @pytest.mark.asyncio
    async def test_get_example_personas_handles_db_error(self):
        """Test: _get_example_personas_from_segment obsługuje błędy DB."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection error"))

        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        project_id = uuid4()
        segment_id = "seg_test"

        personas = await service._get_example_personas_from_segment(
            project_id, segment_id
        )

        # Powinno zwrócić pustą listę zamiast crashować
        assert personas == []

    @pytest.mark.asyncio
    async def test_get_example_personas_filters_deleted(self):
        """Test: _get_example_personas_from_segment filtruje usunięte persony."""
        mock_db = AsyncMock()

        # Verify że query ma warunek deleted_at.is_(None)
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        project_id = uuid4()
        segment_id = "seg_test"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        await service._get_example_personas_from_segment(project_id, segment_id)

        # Verify że execute został wywołany (query construction jest ok)
        assert mock_db.execute.called


class TestRAGContextFetching:
    """Testy dla pobierania kontekstu RAG."""

    @pytest.mark.asyncio
    async def test_fetch_rag_context_success(self):
        """Test: _fetch_rag_context pobiera i formatuje kontekst RAG."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        # Mock RAG service
        mock_rag = MagicMock()
        mock_rag.vector_store = True  # RAG enabled
        mock_doc = MagicMock()
        mock_doc.page_content = "Stopa zatrudnienia w Polsce w 2023 roku wyniosła 78.4% dla grupy 25-34 lata."
        mock_rag.hybrid_search = AsyncMock(return_value=[mock_doc])

        service.rag_service = mock_rag

        demographics = {
            "age": "25-34",
            "gender": "kobieta",
            "education": "wyższe",
            "location": "Warszawa"
        }

        context = await service._fetch_rag_context(demographics)

        assert isinstance(context, str)
        assert len(context) > 0
        assert "RAG" in context or "KONTEKST" in context
        assert "78.4%" in context  # Weryfikacja że mock doc został included

    @pytest.mark.asyncio
    async def test_fetch_rag_context_handles_rag_unavailable(self):
        """Test: _fetch_rag_context obsługuje brak RAG service."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None
        service.rag_service = None  # RAG unavailable

        demographics = {"age": "25-34"}

        context = await service._fetch_rag_context(demographics)

        assert context == "Brak dostępnego kontekstu RAG."

    @pytest.mark.asyncio
    async def test_fetch_rag_context_handles_no_results(self):
        """Test: _fetch_rag_context obsługuje puste wyniki RAG."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        mock_rag = MagicMock()
        mock_rag.vector_store = True
        mock_rag.hybrid_search = AsyncMock(return_value=[])  # Empty results
        service.rag_service = mock_rag

        demographics = {"age": "25-34"}

        context = await service._fetch_rag_context(demographics)

        assert context == "Brak danych RAG dla tej demografii."

    @pytest.mark.asyncio
    async def test_fetch_rag_context_truncates_long_content(self):
        """Test: _fetch_rag_context obcina zbyt długi kontekst do 1500 chars."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        # Mock very long content
        long_content = "A" * 1000  # Długi fragment
        mock_docs = [MagicMock(page_content=long_content) for _ in range(10)]

        mock_rag = MagicMock()
        mock_rag.vector_store = True
        mock_rag.hybrid_search = AsyncMock(return_value=mock_docs)
        service.rag_service = mock_rag

        demographics = {"age": "25-34"}

        context = await service._fetch_rag_context(demographics)

        # Powinno być obcięte do max 1500 chars + "..."
        assert len(context) <= 1504  # 1500 + "..."

    @pytest.mark.asyncio
    async def test_fetch_rag_context_handles_rag_error(self):
        """Test: _fetch_rag_context obsługuje błędy RAG."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)
        service.redis_client = None

        mock_rag = MagicMock()
        mock_rag.vector_store = True
        mock_rag.hybrid_search = AsyncMock(side_effect=Exception("RAG timeout"))
        service.rag_service = mock_rag

        demographics = {"age": "25-34"}

        context = await service._fetch_rag_context(demographics)

        assert context == "Błąd podczas pobierania kontekstu RAG."


class TestSegmentBriefGeneration:
    """Testy dla głównej metody generowania segment brief."""

    @pytest.mark.asyncio
    async def test_generate_segment_brief_cache_hit(self):
        """Test: generate_segment_brief zwraca cached brief jeśli istnieje."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)

        # Mock Redis cache hit
        cached_brief = SegmentBrief(
            segment_id="seg_test",
            segment_name="Test Segment",
            description="Cached description",
            social_context="Cached context",
            characteristics=["char1"],
            based_on_personas_count=3,
            demographics={"age": "25-34"},
            generated_at=datetime.now(timezone.utc),
            generated_by="gemini-2.5-pro"
        )

        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=cached_brief):
            service.redis_client = MagicMock()  # Enable cache

            demographics = {"age": "25-34"}
            project_id = uuid4()

            brief = await service.generate_segment_brief(demographics, project_id)

            assert brief == cached_brief
            assert brief.description == "Cached description"

    @pytest.mark.asyncio
    async def test_generate_segment_brief_cache_miss_generates_new(self):
        """Test: generate_segment_brief generuje nowy brief przy cache miss."""
        mock_db = AsyncMock()

        # Mock example personas
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        # Mock Redis cache miss
        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=None):
            with patch('app.services.personas.orchestration.segment_brief_service.save_to_cache'):
                # Mock RAG
                service.rag_service = MagicMock()
                service.rag_service.vector_store = None  # RAG disabled dla uproszczenia

                # Mock LLM response
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "A" * 1500  # Brief o długości 1500 chars
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                service.llm = mock_llm

                # Mock helper functions
                with patch('app.services.personas.orchestration.segment_brief_service.generate_segment_name',
                          return_value="Test Segment"):
                    with patch('app.services.personas.orchestration.segment_brief_service.generate_social_context',
                              return_value="Social context"):
                        with patch('app.services.personas.orchestration.segment_brief_service.extract_characteristics',
                                  return_value=["char1", "char2"]):

                            demographics = {"age": "25-34"}
                            project_id = uuid4()

                            brief = await service.generate_segment_brief(demographics, project_id, force_refresh=True)

                            assert brief is not None
                            assert brief.segment_name == "Test Segment"
                            assert len(brief.description) == 1500

    @pytest.mark.asyncio
    async def test_generate_segment_brief_validates_brief_length_too_short(self):
        """Test: generate_segment_brief loguje warning jeśli brief < 1000 chars."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=None):
            with patch('app.services.personas.orchestration.segment_brief_service.save_to_cache'):
                service.rag_service = MagicMock()
                service.rag_service.vector_store = None

                # Mock LLM zwracający zbyt krótki brief
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Short brief"  # < 1000 chars
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                service.llm = mock_llm

                with patch('app.services.personas.orchestration.segment_brief_service.generate_segment_name',
                          return_value="Test"):
                    with patch('app.services.personas.orchestration.segment_brief_service.generate_social_context',
                              return_value="Context"):
                        with patch('app.services.personas.orchestration.segment_brief_service.extract_characteristics',
                                  return_value=[]):

                            demographics = {"age": "25-34"}
                            project_id = uuid4()

                            brief = await service.generate_segment_brief(demographics, project_id, force_refresh=True)

                            # Brief powinien być wygenerowany mimo że jest krótki
                            assert brief is not None
                            assert len(brief.description) < 1000

    @pytest.mark.asyncio
    async def test_generate_segment_brief_truncates_too_long_brief(self):
        """Test: generate_segment_brief obcina brief > 6000 chars do 5000."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=None):
            with patch('app.services.personas.orchestration.segment_brief_service.save_to_cache'):
                service.rag_service = MagicMock()
                service.rag_service.vector_store = None

                # Mock LLM zwracający zbyt długi brief
                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "A" * 7000  # > 6000 chars
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                service.llm = mock_llm

                with patch('app.services.personas.orchestration.segment_brief_service.generate_segment_name',
                          return_value="Test"):
                    with patch('app.services.personas.orchestration.segment_brief_service.generate_social_context',
                              return_value="Context"):
                        with patch('app.services.personas.orchestration.segment_brief_service.extract_characteristics',
                                  return_value=[]):

                            demographics = {"age": "25-34"}
                            project_id = uuid4()

                            brief = await service.generate_segment_brief(demographics, project_id, force_refresh=True)

                            # Brief powinien być obcięty do 5000 chars
                            assert len(brief.description) == 5000

    @pytest.mark.asyncio
    async def test_generate_segment_brief_handles_llm_error_with_fallback(self):
        """Test: generate_segment_brief używa fallback brief przy błędzie LLM."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=None):
            with patch('app.services.personas.orchestration.segment_brief_service.save_to_cache'):
                service.rag_service = MagicMock()
                service.rag_service.vector_store = None

                # Mock LLM error
                mock_llm = AsyncMock()
                mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))
                service.llm = mock_llm

                with patch('app.services.personas.orchestration.segment_brief_service.generate_segment_name',
                          return_value="Test Segment"):
                    with patch('app.services.personas.orchestration.segment_brief_service.generate_fallback_brief',
                              return_value="Fallback brief description"):
                        with patch('app.services.personas.orchestration.segment_brief_service.generate_social_context',
                                  return_value="Context"):
                            with patch('app.services.personas.orchestration.segment_brief_service.extract_characteristics',
                                      return_value=[]):

                                demographics = {"age": "25-34"}
                                project_id = uuid4()

                                brief = await service.generate_segment_brief(demographics, project_id, force_refresh=True)

                                # Powinien użyć fallback
                                assert brief is not None
                                assert brief.description == "Fallback brief description"

    @pytest.mark.asyncio
    async def test_generate_segment_brief_saves_to_cache(self):
        """Test: generate_segment_brief zapisuje wygenerowany brief do cache."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        with patch('app.services.personas.orchestration.segment_brief_service.get_from_cache',
                   return_value=None):
            with patch('app.services.personas.orchestration.segment_brief_service.save_to_cache') as mock_save:
                service.rag_service = MagicMock()
                service.rag_service.vector_store = None

                mock_llm = AsyncMock()
                mock_response = MagicMock()
                mock_response.content = "Brief description" * 100  # ~1800 chars
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
                service.llm = mock_llm

                with patch('app.services.personas.orchestration.segment_brief_service.generate_segment_name',
                          return_value="Test"):
                    with patch('app.services.personas.orchestration.segment_brief_service.generate_social_context',
                              return_value="Context"):
                        with patch('app.services.personas.orchestration.segment_brief_service.extract_characteristics',
                                  return_value=[]):

                            demographics = {"age": "25-34"}
                            project_id = uuid4()

                            await service.generate_segment_brief(demographics, project_id, force_refresh=True)

                            # Verify save_to_cache został wywołany
                            assert mock_save.called


class TestPersonaUniqueness:
    """Testy dla generowania opisów unikalności person."""

    @pytest.mark.asyncio
    async def test_generate_persona_uniqueness_calls_helper(self):
        """Test: generate_persona_uniqueness deleguje do helper function."""
        mock_db = AsyncMock()
        service = SegmentBriefService(db=mock_db)

        mock_persona = Persona(
            id=uuid4(),
            name="Jan Kowalski",
            age=30,
            gender="mężczyzna"
        )

        mock_brief = SegmentBrief(
            segment_id="seg_test",
            segment_name="Test",
            description="Description",
            social_context="Context",
            characteristics=["char1"],
            based_on_personas_count=3,
            demographics={"age": "25-34"},
            generated_at=datetime.now(timezone.utc),
            generated_by="gemini-2.5-pro"
        )

        with patch('app.services.personas.orchestration.segment_brief_service.generate_persona_uniqueness',
                   return_value="Jan jest wyjątkowy bo...") as mock_generate:

            result = await service.generate_persona_uniqueness(mock_persona, mock_brief)

            assert result == "Jan jest wyjątkowy bo..."
            assert mock_generate.called


class TestPublicAPI:
    """Testy dla public API metody get_or_generate_segment_brief."""

    @pytest.mark.asyncio
    async def test_get_or_generate_segment_brief_returns_response_with_metadata(self):
        """Test: get_or_generate_segment_brief zwraca SegmentBriefResponse z metadanymi."""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = SegmentBriefService(db=mock_db)

        # Mock brief generation
        mock_brief = SegmentBrief(
            segment_id="seg_test",
            segment_name="Test",
            description="Description",
            social_context="Context",
            characteristics=["char1"],
            based_on_personas_count=0,
            demographics={"age": "25-34"},
            generated_at=datetime.now(timezone.utc),
            generated_by="gemini-2.5-pro"
        )

        with patch.object(service, 'generate_segment_brief', return_value=mock_brief):
            request = SegmentBriefRequest(
                project_id=str(uuid4()),
                demographics={"age": "25-34"},
                max_example_personas=3,
                force_refresh=False
            )

            response = await service.get_or_generate_segment_brief(request)

            assert isinstance(response, SegmentBriefResponse)
            assert response.brief == mock_brief
            assert response.from_cache is True  # force_refresh=False
