"""
Unit tests for Polish insight type classification

Tests the _classify_insight_type method from DiscussionSummarizer
with Polish text examples to ensure proper classification into:
- opportunity (szanse)
- risk (ryzyka)
- trend (trendy)
- pattern (wzorce)
"""

import pytest
from app.services.focus_groups.discussion_summarizer import DiscussionSummarizer


@pytest.fixture
def summarizer():
    """Create a DiscussionSummarizer instance for testing."""
    return DiscussionSummarizer()


class TestPolishInsightClassification:
    """Test suite for Polish insight type classification."""

    # =========================================================================
    # OPPORTUNITY TESTS
    # =========================================================================

    def test_opportunity_polish_basic(self, summarizer):
        """Test opportunity classification with basic Polish keywords."""
        text = "To duża szansa na wzrost sprzedaży o 30%."
        assert summarizer._classify_insight_type(text) == "opportunity"

    def test_opportunity_polish_potential(self, summarizer):
        """Test opportunity with 'potencjał' keyword."""
        text = "Widzimy ogromny potencjał w segmencie młodych klientów."
        assert summarizer._classify_insight_type(text) == "opportunity"

    def test_opportunity_polish_advantage(self, summarizer):
        """Test opportunity with 'przewaga' keyword."""
        text = "Nasza przewaga konkurencyjna może przynieść korzyści finansowe."
        assert summarizer._classify_insight_type(text) == "opportunity"

    def test_opportunity_english(self, summarizer):
        """Test opportunity classification with English keywords."""
        text = "This is a great opportunity for growth and improvement."
        assert summarizer._classify_insight_type(text) == "opportunity"

    # =========================================================================
    # RISK TESTS
    # =========================================================================

    def test_risk_polish_basic(self, summarizer):
        """Test risk classification with basic Polish keywords."""
        text = "Istotne ryzyko odpływu klientów do konkurencji."
        assert summarizer._classify_insight_type(text) == "risk"

    def test_risk_polish_threat(self, summarizer):
        """Test risk with 'zagrożenie' keyword."""
        text = "Główne zagrożenie to rosnące koszty surowców."
        assert summarizer._classify_insight_type(text) == "risk"

    def test_risk_polish_problem(self, summarizer):
        """Test risk with 'problem' keyword."""
        text = "Kluczowy problem to brak kompetencji w zespole."
        assert summarizer._classify_insight_type(text) == "risk"

    def test_risk_polish_challenge(self, summarizer):
        """Test risk with 'wyzwanie' keyword."""
        text = "Największe wyzwanie to utrzymanie jakości przy obniżaniu cen."
        assert summarizer._classify_insight_type(text) == "risk"

    def test_risk_english(self, summarizer):
        """Test risk classification with English keywords."""
        text = "Major concern about customer churn and market threats."
        assert summarizer._classify_insight_type(text) == "risk"

    # =========================================================================
    # TREND TESTS
    # =========================================================================

    def test_trend_polish_basic(self, summarizer):
        """Test trend classification with basic Polish keywords."""
        text = "Widać wyraźny trend rosnący w kategorii produktów premium."
        assert summarizer._classify_insight_type(text) == "trend"

    def test_trend_polish_change(self, summarizer):
        """Test trend with 'zmiana' keyword."""
        text = "Zaobserwowaliśmy znaczącą zmianę w preferencjach zakupowych."
        assert summarizer._classify_insight_type(text) == "trend"

    def test_trend_polish_increasing(self, summarizer):
        """Test trend with 'coraz więcej' phrase."""
        text = "Coraz więcej klientów wybiera opcję subskrypcyjną."
        assert summarizer._classify_insight_type(text) == "trend"

    def test_trend_polish_decreasing(self, summarizer):
        """Test trend with 'coraz mniej' phrase."""
        text = "Coraz mniej osób korzysta z tradycyjnych kanałów sprzedaży."
        assert summarizer._classify_insight_type(text) == "trend"

    def test_trend_english(self, summarizer):
        """Test trend classification with English keywords."""
        text = "There's an increasing shift towards mobile-first experiences."
        assert summarizer._classify_insight_type(text) == "trend"

    # =========================================================================
    # PATTERN TESTS
    # =========================================================================

    def test_pattern_polish_basic(self, summarizer):
        """Test pattern classification with basic Polish keywords."""
        text = "Regularny wzorzec zachowań zakupowych w weekendy."
        assert summarizer._classify_insight_type(text) == "pattern"

    def test_pattern_polish_consistent(self, summarizer):
        """Test pattern with 'konsekwentny' keyword."""
        text = "Konsekwentne wybieranie najtańszych opcji przez większość klientów."
        assert summarizer._classify_insight_type(text) == "pattern"

    def test_pattern_polish_frequent(self, summarizer):
        """Test pattern with 'częsty' keyword."""
        text = "Częsty wzorzec: użytkownicy porzucają koszyk przy wysyłce."
        assert summarizer._classify_insight_type(text) == "pattern"

    def test_pattern_polish_majority(self, summarizer):
        """Test pattern with 'większość' keyword."""
        text = "Większość respondentów wykazuje podobne zachowania przy wyborze produktu."
        assert summarizer._classify_insight_type(text) == "pattern"

    def test_pattern_english(self, summarizer):
        """Test pattern classification with English keywords."""
        text = "Consistent pattern across all user segments and demographics."
        assert summarizer._classify_insight_type(text) == "pattern"

    # =========================================================================
    # MIXED & EDGE CASES
    # =========================================================================

    def test_mixed_keywords_priority_opportunity(self, summarizer):
        """Test that opportunity keywords have highest priority."""
        # Contains both "problem" (risk) and "szansa" (opportunity)
        # Should classify as opportunity (higher priority)
        text = "Problem to też szansa na ulepszenie naszego procesu."
        assert summarizer._classify_insight_type(text) == "opportunity"

    def test_mixed_keywords_priority_risk(self, summarizer):
        """Test risk priority over trend."""
        # Contains both "zmiana" (trend) and "ryzyko" (risk)
        # Should classify as risk (higher priority than trend)
        text = "Zmiana regulacji niesie ryzyko opóźnień w projekcie."
        assert summarizer._classify_insight_type(text) == "risk"

    def test_fallback_default_opportunity(self, summarizer):
        """Test default fallback to opportunity for generic text."""
        # Text with no specific keywords should default to "opportunity"
        text = "Klienci oczekują lepszej jakości obsługi."
        result = summarizer._classify_insight_type(text)
        # Should be opportunity (default fallback)
        assert result == "opportunity"

    def test_fallback_time_indicator_trend(self, summarizer):
        """Test fallback with time indicators defaults to trend."""
        text = "W ostatnim czasie obserwujemy nowe zachowania konsumentów."
        result = summarizer._classify_insight_type(text)
        assert result == "trend"

    def test_empty_text(self, summarizer):
        """Test classification with empty text."""
        result = summarizer._classify_insight_type("")
        # Empty text should still return a valid type (fallback to opportunity)
        assert result == "opportunity"

    def test_case_insensitive(self, summarizer):
        """Test that classification is case-insensitive."""
        text_lower = "duża szansa na wzrost"
        text_upper = "DUŻA SZANSA NA WZROST"
        text_mixed = "Duża Szansa Na Wzrost"

        assert summarizer._classify_insight_type(text_lower) == "opportunity"
        assert summarizer._classify_insight_type(text_upper) == "opportunity"
        assert summarizer._classify_insight_type(text_mixed) == "opportunity"

    # =========================================================================
    # BILINGUAL TESTS
    # =========================================================================

    def test_bilingual_opportunity(self, summarizer):
        """Test classification with mixed Polish-English text (opportunity)."""
        text = "Excellent szansa for market expansion i wzrost revenue."
        assert summarizer._classify_insight_type(text) == "opportunity"

    def test_bilingual_risk(self, summarizer):
        """Test classification with mixed Polish-English text (risk)."""
        text = "Major problem z jakością and increasing ryzyko recalls."
        assert summarizer._classify_insight_type(text) == "risk"


# =========================================================================
# PARAMETRIZED TESTS FOR COMPREHENSIVE COVERAGE
# =========================================================================

@pytest.mark.parametrize(
    "text,expected_type",
    [
        # Polish opportunities
        ("Okazja do ekspansji na nowe rynki", "opportunity"),
        ("Korzyści z wdrożenia nowej technologii", "opportunity"),
        ("Innowacyjne rozwiązanie przyniesie zyski", "opportunity"),

        # Polish risks
        ("Obawa o utratę kluczowych klientów", "risk"),
        ("Bariera w postaci wysokich kosztów", "risk"),
        ("Kryzys finansowy może wpłynąć negatywnie", "risk"),

        # Polish trends
        ("Dynamika rynku wskazuje na wzrost popytu", "trend"),
        ("Ewolucja preferencji konsumenckich", "trend"),
        ("Stopniowe przesunięcie w kierunku ekologii", "trend"),

        # Polish patterns
        ("Typowe zachowanie dla tego segmentu", "pattern"),
        ("Systematyczne pomijanie niektórych opcji", "pattern"),
        ("Powszechny schemat działania użytkowników", "pattern"),

        # English
        ("Great potential for innovation", "opportunity"),
        ("Significant threat from competitors", "risk"),
        ("Growing tendency in the market", "trend"),
        ("Common behavior across users", "pattern"),
    ],
)
def test_classification_parametrized(summarizer, text, expected_type):
    """Parametrized test covering various Polish and English examples."""
    assert summarizer._classify_insight_type(text) == expected_type
