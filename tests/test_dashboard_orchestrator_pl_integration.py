"""
Integration tests for Dashboard Orchestrator with Polish content

Tests the complete flow of insight analytics with Polish text:
1. InsightEvidence with Polish content
2. Insight type classification
3. Concept extraction
4. Response pattern detection
5. Analytics generation

These are integration tests that require database fixtures.
"""

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InsightEvidence, Project, FocusGroup
from app.services.dashboard.dashboard_orchestrator import DashboardOrchestrator


@pytest.fixture
async def polish_test_project(db_session: AsyncSession):
    """Create a test project for Polish content testing."""
    project = Project(
        name="Test Project - Polski",
        description="Projekt testowy z polskimi insightami",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def polish_focus_group(db_session: AsyncSession, polish_test_project: Project):
    """Create a test focus group."""
    focus_group = FocusGroup(
        project_id=polish_test_project.id,
        name="Grupa fokusowa - jakość produktu",
        status="completed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(focus_group)
    await db_session.commit()
    await db_session.refresh(focus_group)
    return focus_group


@pytest.fixture
async def polish_insights(db_session: AsyncSession, polish_focus_group: FocusGroup):
    """Create test insights with Polish content."""
    insights = [
        # OPPORTUNITY - szansa
        InsightEvidence(
            insight="Duża szansa na wzrost w segmencie młodych klientów poprzez poprawę jakości obsługi.",
            insight_type="opportunity",  # Will be re-classified
            confidence_score=0.85,
            impact_score=8,
            sentiment="positive",
            concepts=["szansa", "wzrost", "klienci", "jakość", "obsługa"],
            evidence=[
                {"text": "Młodzi klienci oczekują lepszej obsługi klienta i wsparcia technicznego."},
                {"text": "Jakość produktu jest wysoka, ale cena może być barierą."}
            ],
            sources=["persona_1", "persona_2"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        ),
        # RISK - ryzyko
        InsightEvidence(
            insight="Istotne ryzyko odpływu klientów z powodu wysokich cen i słabej wydajności aplikacji.",
            insight_type="risk",
            confidence_score=0.90,
            impact_score=9,
            sentiment="negative",
            concepts=["ryzyko", "odpływ", "cena", "wydajność", "aplikacja"],
            evidence=[
                {"text": "Ceny są zbyt wysokie w porównaniu do konkurencji."},
                {"text": "Aplikacja działa wolno i często się zacina podczas użytkowania."}
            ],
            sources=["persona_3", "persona_4"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        ),
        # TREND - trend
        InsightEvidence(
            insight="Rosnący trend przechodzenia na modele subskrypcyjne zamiast jednorazowych zakupów.",
            insight_type="trend",
            confidence_score=0.80,
            impact_score=7,
            sentiment="neutral",
            concepts=["trend", "subskrypcja", "zakupy", "model"],
            evidence=[
                {"text": "Coraz więcej klientów preferuje miesięczne subskrypcje."},
                {"text": "Zmiana w zachowaniach zakupowych jest widoczna od roku."}
            ],
            sources=["persona_5"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        ),
        # PATTERN - wzorzec
        InsightEvidence(
            insight="Wszyscy użytkownicy konsekwentnie pomijają funkcję eksportu danych w formatach zaawansowanych.",
            insight_type="pattern",
            confidence_score=0.75,
            impact_score=5,
            sentiment="neutral",
            concepts=["użytkownicy", "funkcja", "eksport", "dane"],
            evidence=[
                {"text": "Większość respondentów nie korzysta z zaawansowanego eksportu."},
                {"text": "Typowy wzorzec: eksport tylko do PDF i Excel podstawowego."}
            ],
            sources=["persona_6", "persona_7"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        ),
        # MIXED - brakujące funkcje
        InsightEvidence(
            insight="Brakuje funkcji integracji z popularnymi narzędziami CRM, co utrudnia wdrożenie.",
            insight_type="opportunity",  # Should be classified based on keywords
            confidence_score=0.70,
            impact_score=6,
            sentiment="mixed",
            concepts=["brak", "funkcja", "integracja", "CRM", "wdrożenie"],
            evidence=[
                {"text": "Klienci chcieliby dodać integrację z Salesforce i HubSpot."},
                {"text": "Brak API uniemożliwia automatyzację procesów biznesowych."}
            ],
            sources=["persona_8"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        ),
    ]

    for insight in insights:
        db_session.add(insight)

    await db_session.commit()

    # Refresh to get IDs
    for insight in insights:
        await db_session.refresh(insight)

    return insights


@pytest.mark.asyncio
@pytest.mark.integration
class TestDashboardOrchestratorPolishIntegration:
    """Integration test suite for Dashboard Orchestrator with Polish content."""

    async def test_insight_analytics_with_polish_content(
        self,
        db_session: AsyncSession,
        polish_focus_group: FocusGroup,
        polish_insights: list[InsightEvidence],
    ):
        """
        Test complete insight analytics flow with Polish content.

        Verifies:
        1. Insight type distribution (not 100% pattern)
        2. Top concepts don't contain stopwords
        3. Response patterns detect Polish keywords
        4. Sentiment distribution is calculated
        """
        # Create orchestrator
        orchestrator = DashboardOrchestrator(db_session)

        # Get analytics
        analytics = await orchestrator.get_insight_analytics(
            focus_group_id=polish_focus_group.id
        )

        # =====================================================================
        # 1. VERIFY INSIGHT TYPE DISTRIBUTION
        # =====================================================================
        assert "insight_types" in analytics
        insight_types = analytics["insight_types"]

        # Should have all 4 types represented
        assert "opportunity" in insight_types
        assert "risk" in insight_types
        assert "trend" in insight_types
        assert "pattern" in insight_types

        # Pattern should NOT be 100% (the original bug)
        total_insights = sum(insight_types.values())
        assert total_insights == len(polish_insights)

        pattern_percentage = (insight_types["pattern"] / total_insights) * 100
        assert pattern_percentage < 100, "Pattern type should not dominate 100%"
        assert pattern_percentage < 50, "Pattern type should be less than 50%"

        # Should have meaningful distribution
        assert insight_types["opportunity"] > 0, "Should have at least one opportunity"
        assert insight_types["risk"] > 0, "Should have at least one risk"
        assert insight_types["trend"] > 0, "Should have at least one trend"

        # =====================================================================
        # 2. VERIFY TOP CONCEPTS (No stopwords)
        # =====================================================================
        assert "top_concepts" in analytics
        top_concepts = analytics["top_concepts"]

        # Should have concepts
        assert len(top_concepts) > 0, "Should extract top concepts"

        # Extract concept names
        concept_names = [c["concept"] for c in top_concepts]

        # Should NOT contain problematic stopwords from original bug
        problematic_stopwords = ["jest", "brak", "czas", "czasu"]
        for stopword in problematic_stopwords:
            assert stopword not in concept_names, \
                f"Stopword '{stopword}' should not be in top concepts"

        # Should contain meaningful concepts (at least some)
        meaningful_concepts = [
            "jakość", "obsług", "cena", "wydajność", "aplikacj",  # May be normalized
            "klient", "produkt", "funkcj", "integracja", "subskrypcj"
        ]

        found_meaningful = sum(
            1 for concept in concept_names
            for meaningful in meaningful_concepts
            if meaningful in concept.lower()
        )

        assert found_meaningful >= 3, \
            f"Should have at least 3 meaningful concepts, found {found_meaningful}"

        # =====================================================================
        # 3. VERIFY RESPONSE PATTERNS (Polish keyword detection)
        # =====================================================================
        assert "response_patterns" in analytics
        response_patterns = analytics["response_patterns"]

        # Should detect patterns
        assert len(response_patterns) > 0, "Should detect response patterns"

        # Extract pattern labels
        pattern_labels = [p["pattern"] for p in response_patterns]

        # Should detect some expected patterns based on our test data:
        # - "Wrażliwość cenowa" (from "ceny", "koszt" keywords)
        # - "Problemy wydajnościowe" (from "wydajność", "wolno", "zacina")
        # - "Jakość produktu" (from "jakość")
        # - "Brakujące funkcje" (from "brakuje", "funkcja")

        expected_patterns = [
            "Wrażliwość cenowa",
            "Problemy wydajnościowe",
            "Jakość produktu",
            "Brakujące funkcje",
        ]

        detected_expected = sum(
            1 for pattern in pattern_labels
            if pattern in expected_patterns
        )

        # Should detect at least 2 of the expected patterns
        assert detected_expected >= 2, \
            f"Should detect at least 2 expected patterns, found {detected_expected}: {pattern_labels}"

        # =====================================================================
        # 4. VERIFY SENTIMENT DISTRIBUTION
        # =====================================================================
        assert "sentiment_distribution" in analytics
        sentiment_dist = analytics["sentiment_distribution"]

        # Should have sentiment data
        assert sum(sentiment_dist.values()) == total_insights

        # Based on our test data:
        # - 1 positive (opportunity)
        # - 1 negative (risk)
        # - 2 neutral (trend, pattern)
        # - 1 mixed (missing features)
        assert sentiment_dist.get("positive", 0) >= 1
        assert sentiment_dist.get("negative", 0) >= 1
        assert sentiment_dist.get("neutral", 0) >= 1


    async def test_no_insights_returns_empty_analytics(
        self,
        db_session: AsyncSession,
        polish_test_project: Project,
    ):
        """Test that empty focus group returns valid but empty analytics."""
        # Create empty focus group
        empty_fg = FocusGroup(
            project_id=polish_test_project.id,
            name="Empty group",
            status="completed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(empty_fg)
        await db_session.commit()
        await db_session.refresh(empty_fg)

        # Get analytics
        orchestrator = DashboardOrchestrator(db_session)
        analytics = await orchestrator.get_insight_analytics(focus_group_id=empty_fg.id)

        # Should return valid structure with zeros/empty lists
        assert analytics["insight_types"] == {
            "opportunity": 0,
            "risk": 0,
            "trend": 0,
            "pattern": 0,
        }
        assert analytics["top_concepts"] == []
        assert analytics["response_patterns"] == []
        assert analytics["sentiment_distribution"] == {}


    async def test_multilingual_insights(
        self,
        db_session: AsyncSession,
        polish_focus_group: FocusGroup,
    ):
        """Test analytics with mixed Polish-English content."""
        # Create bilingual insights
        bilingual_insight = InsightEvidence(
            insight="Great opportunity dla ekspansji na polski rynek z high quality produktami.",
            insight_type="opportunity",
            confidence_score=0.80,
            impact_score=7,
            sentiment="positive",
            concepts=["opportunity", "ekspansja", "rynek", "quality", "produkty"],
            evidence=[
                {"text": "Polish market ma huge potential for growth i innovation."},
                {"text": "Customer service needs improvement ale product quality jest excellent."}
            ],
            sources=["persona_9"],
            focus_group_id=polish_focus_group.id,
            created_at=datetime.utcnow(),
        )
        db_session.add(bilingual_insight)
        await db_session.commit()

        # Get analytics
        orchestrator = DashboardOrchestrator(db_session)
        analytics = await orchestrator.get_insight_analytics(focus_group_id=polish_focus_group.id)

        # Should handle bilingual content
        assert analytics is not None
        assert "insight_types" in analytics
        assert "top_concepts" in analytics

        # Should extract concepts from both languages
        concept_names = [c["concept"] for c in analytics["top_concepts"]]
        # May contain both Polish and English concepts
        assert len(concept_names) > 0


# =========================================================================
# PERFORMANCE TESTS (Optional)
# =========================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestDashboardPerformancePolish:
    """Performance tests for dashboard analytics with Polish content."""

    async def test_large_dataset_performance(
        self,
        db_session: AsyncSession,
        polish_focus_group: FocusGroup,
    ):
        """Test analytics performance with large number of Polish insights."""
        import time

        # Create 100 insights
        insights = []
        for i in range(100):
            insight = InsightEvidence(
                insight=f"Test insight {i}: Jakość produktu i obsługa klienta wymagają poprawy.",
                insight_type="opportunity",
                confidence_score=0.75,
                impact_score=5,
                sentiment="neutral",
                concepts=["jakość", "produkt", "obsługa", "klient"],
                evidence=[{"text": f"Evidence {i}"}],
                sources=[f"persona_{i}"],
                focus_group_id=polish_focus_group.id,
                created_at=datetime.utcnow(),
            )
            insights.append(insight)

        db_session.add_all(insights)
        await db_session.commit()

        # Measure performance
        orchestrator = DashboardOrchestrator(db_session)

        start_time = time.time()
        analytics = await orchestrator.get_insight_analytics(focus_group_id=polish_focus_group.id)
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds for 100 insights)
        assert elapsed < 5.0, f"Analytics took too long: {elapsed:.2f}s"

        # Should return valid results
        assert analytics is not None
        assert sum(analytics["insight_types"].values()) == 100
