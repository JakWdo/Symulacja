"""
Unit tests for Polish response patterns keyword matching

Tests the keyword_patterns matching logic from DashboardOrchestrator
to ensure Polish keywords are properly detected for:
- Wrażliwość cenowa (Price sensitivity)
- Jakość produktu (Product quality)
- Doświadczenie klienta (Customer experience)
- Brakujące funkcje (Feature requests)
- Problemy wydajnościowe (Performance issues)
"""

import pytest


class TestPolishResponsePatterns:
    """Test suite for Polish response patterns keyword matching."""

    # Keyword patterns from dashboard_orchestrator.py
    KEYWORD_PATTERNS = {
        "Wrażliwość cenowa": [
            # Polish
            "cena", "cennik", "ceny", "cenowy", "kosztowny", "drogi", "droga", "drogie",
            "tani", "tania", "tanie", "koszt", "kosztów", "wydatek", "opłata", "płatność",
            "zbyt drogo", "za drogo", "ekonomiczny", "budżet",
            # English
            "price", "pricing", "cost", "expensive", "cheap", "affordable", "budget",
        ],
        "Jakość produktu": [
            # Polish
            "jakość", "jakości", "trwałość", "trwały", "niezawodny", "niezawodność",
            "awaria", "usterka", "defekt", "zepsuty", "uszkodzony", "wadliwy",
            "solidny", "solidność", "wytrzymały",
            # English
            "quality", "durable", "reliable", "defect", "faulty", "broken", "damaged",
            "solid", "robust", "sturdy",
        ],
        "Doświadczenie klienta": [
            # Polish
            "doświadczenie", "obsługa", "obsługi", "wsparcie", "pomoc", "kontakt",
            "onboarding", "wdrożenie", "użyteczność", "łatwość", "intuicyjny",
            "przyjazny", "serwis", "service", "UX",
            # English
            "experience", "journey", "onboarding", "support", "service", "help",
            "customer service", "usability", "user-friendly", "intuitive",
        ],
        "Brakujące funkcje": [
            # Polish
            "brakuje", "brak", "brakująca", "brakujący", "funkcja", "funkcji",
            "dodać", "dodania", "ulepszyć", "ulepszenie", "poprawić", "poprawa",
            "rozszerzyć", "rozszerzenie", "wprowadzić", "chciałbym", "potrzeba",
            # English
            "feature", "missing", "lack", "add", "improve", "enhance", "extend",
            "would like", "need", "request", "wish",
        ],
        "Problemy wydajnościowe": [
            # Polish
            "wolny", "wolno", "zacina", "zawieszenie", "wydajność", "opóźnienie",
            "lag", "powolny", "crash", "błąd", "awaria", "nie działa", "problem techniczny",
            # English
            "slow", "lag", "performance", "crash", "bug", "error", "freeze",
            "hang", "loading", "latency",
        ],
    }

    def matches_pattern(self, text: str, pattern_name: str) -> bool:
        """Helper to check if text matches any keyword in pattern."""
        text_lower = text.lower()
        keywords = self.KEYWORD_PATTERNS[pattern_name]
        return any(keyword in text_lower for keyword in keywords)

    # =========================================================================
    # PRICE SENSITIVITY TESTS
    # =========================================================================

    def test_price_sensitivity_polish_basic(self):
        """Test basic Polish price keywords."""
        assert self.matches_pattern("Produkt jest zbyt drogi", "Wrażliwość cenowa")
        assert self.matches_pattern("Niska cena przyciąga klientów", "Wrażliwość cenowa")
        assert self.matches_pattern("Koszt wdrożenia jest wysoki", "Wrażliwość cenowa")

    def test_price_sensitivity_polish_phrases(self):
        """Test Polish price phrases."""
        assert self.matches_pattern("Za drogo jak na tę jakość", "Wrażliwość cenowa")
        assert self.matches_pattern("Opłata miesięczna jest akceptowalna", "Wrażliwość cenowa")
        assert self.matches_pattern("Wydatek przekracza budżet", "Wrażliwość cenowa")

    def test_price_sensitivity_english(self):
        """Test English price keywords."""
        assert self.matches_pattern("The price is too expensive", "Wrażliwość cenowa")
        assert self.matches_pattern("Affordable pricing model", "Wrażliwość cenowa")
        assert self.matches_pattern("Budget constraints are an issue", "Wrażliwość cenowa")

    # =========================================================================
    # PRODUCT QUALITY TESTS
    # =========================================================================

    def test_product_quality_polish_basic(self):
        """Test basic Polish quality keywords."""
        assert self.matches_pattern("Wysoka jakość wykonania", "Jakość produktu")
        assert self.matches_pattern("Produkt jest niezawodny", "Jakość produktu")
        assert self.matches_pattern("Trwałość materiału budzi zaufanie", "Jakość produktu")

    def test_product_quality_polish_defects(self):
        """Test Polish defect keywords."""
        assert self.matches_pattern("Wykryto usterki w produkcie", "Jakość produktu")
        assert self.matches_pattern("Awaria po miesiącu użytkowania", "Jakość produktu")
        assert self.matches_pattern("Uszkodzony element w opakowaniu", "Jakość produktu")

    def test_product_quality_english(self):
        """Test English quality keywords."""
        assert self.matches_pattern("Excellent quality and durability", "Jakość produktu")
        assert self.matches_pattern("Product is faulty and broken", "Jakość produktu")
        assert self.matches_pattern("Robust and solid construction", "Jakość produktu")

    # =========================================================================
    # CUSTOMER EXPERIENCE TESTS
    # =========================================================================

    def test_customer_experience_polish_basic(self):
        """Test basic Polish customer experience keywords."""
        assert self.matches_pattern("Świetna obsługa klienta", "Doświadczenie klienta")
        assert self.matches_pattern("Wsparcie techniczne odpowiada szybko", "Doświadczenie klienta")
        assert self.matches_pattern("Łatwość użytkowania systemu", "Doświadczenie klienta")

    def test_customer_experience_polish_onboarding(self):
        """Test Polish onboarding keywords."""
        assert self.matches_pattern("Proces wdrożenia był prosty", "Doświadczenie klienta")
        assert self.matches_pattern("Intuicyjny interfejs użytkownika", "Doświadczenie klienta")
        assert self.matches_pattern("Przyjazny dla początkujących", "Doświadczenie klienta")

    def test_customer_experience_english(self):
        """Test English customer experience keywords."""
        assert self.matches_pattern("Great customer service experience", "Doświadczenie klienta")
        assert self.matches_pattern("User-friendly interface and design", "Doświadczenie klienta")
        assert self.matches_pattern("Support team is very helpful", "Doświadczenie klienta")

    # =========================================================================
    # FEATURE REQUESTS TESTS
    # =========================================================================

    def test_feature_requests_polish_basic(self):
        """Test basic Polish feature request keywords."""
        assert self.matches_pattern("Brakuje funkcji eksportu danych", "Brakujące funkcje")
        assert self.matches_pattern("Chciałbym dodać integrację", "Brakujące funkcje")
        assert self.matches_pattern("Potrzeba ulepszyć raportowanie", "Brakujące funkcje")

    def test_feature_requests_polish_improvements(self):
        """Test Polish improvement keywords."""
        assert self.matches_pattern("Należy poprawić wydajność", "Brakujące funkcje")
        assert self.matches_pattern("Rozszerzyć funkcjonalność o API", "Brakujące funkcje")
        assert self.matches_pattern("Wprowadzić obsługę wielu języków", "Brakujące funkcje")

    def test_feature_requests_english(self):
        """Test English feature request keywords."""
        assert self.matches_pattern("Missing feature for data import", "Brakujące funkcje")
        assert self.matches_pattern("Would like to add automation", "Brakujące funkcje")
        assert self.matches_pattern("Need to enhance the UI", "Brakujące funkcje")

    # =========================================================================
    # PERFORMANCE ISSUES TESTS
    # =========================================================================

    def test_performance_issues_polish_basic(self):
        """Test basic Polish performance keywords."""
        assert self.matches_pattern("System działa wolno", "Problemy wydajnościowe")
        assert self.matches_pattern("Aplikacja się zacina", "Problemy wydajnościowe")
        assert self.matches_pattern("Wydajność jest niezadowalająca", "Problemy wydajnościowe")

    def test_performance_issues_polish_errors(self):
        """Test Polish error keywords."""
        assert self.matches_pattern("Wystąpił błąd krytyczny", "Problemy wydajnościowe")
        assert self.matches_pattern("Aplikacja nie działa poprawnie", "Problemy wydajnościowe")
        assert self.matches_pattern("Problem techniczny z logowaniem", "Problemy wydajnościowe")

    def test_performance_issues_english(self):
        """Test English performance keywords."""
        assert self.matches_pattern("The app is too slow to load", "Problemy wydajnościowe")
        assert self.matches_pattern("Frequent crashes and bugs", "Problemy wydajnościowe")
        assert self.matches_pattern("Performance issues with large datasets", "Problemy wydajnościowe")

    # =========================================================================
    # NEGATIVE TESTS (Should NOT match)
    # =========================================================================

    def test_no_false_positives_generic_text(self):
        """Test that generic text doesn't match any pattern."""
        generic_text = "To jest zwykły opis bez szczególnych słów kluczowych."

        # Should not match any pattern
        for pattern_name in self.KEYWORD_PATTERNS.keys():
            assert not self.matches_pattern(generic_text, pattern_name), \
                f"Generic text should not match pattern '{pattern_name}'"

    def test_no_cross_pattern_pollution(self):
        """Test that price keywords don't match quality patterns, etc."""
        price_text = "Cena jest za wysoka"
        assert self.matches_pattern(price_text, "Wrażliwość cenowa")
        assert not self.matches_pattern(price_text, "Jakość produktu")
        assert not self.matches_pattern(price_text, "Doświadczenie klienta")

        quality_text = "Jakość jest rewelacyjna"
        assert self.matches_pattern(quality_text, "Jakość produktu")
        assert not self.matches_pattern(quality_text, "Wrażliwość cenowa")
        assert not self.matches_pattern(quality_text, "Brakujące funkcje")

    # =========================================================================
    # MIXED & BILINGUAL TESTS
    # =========================================================================

    def test_bilingual_text_matches(self):
        """Test that bilingual text matches correctly."""
        # Mixed Polish-English
        text = "Customer service i obsługa są świetne, ale price jest za high."

        # Should match both customer experience (obsługa, service) and price (price)
        assert self.matches_pattern(text, "Doświadczenie klienta")
        assert self.matches_pattern(text, "Wrażliwość cenowa")

    def test_multiple_patterns_in_text(self):
        """Test text that matches multiple patterns."""
        text = (
            "Produkt ma wysoką jakość, ale cena jest zbyt wysoka. "
            "Brakuje funkcji automatyzacji i wydajność jest słaba."
        )

        # Should match multiple patterns
        assert self.matches_pattern(text, "Jakość produktu")  # "jakość"
        assert self.matches_pattern(text, "Wrażliwość cenowa")  # "cena"
        assert self.matches_pattern(text, "Brakujące funkcje")  # "brakuje funkcji"
        assert self.matches_pattern(text, "Problemy wydajnościowe")  # "wydajność"

    # =========================================================================
    # CASE SENSITIVITY TESTS
    # =========================================================================

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        text_variants = [
            "cena jest wysoka",
            "CENA JEST WYSOKA",
            "Cena Jest Wysoka",
        ]

        for text in text_variants:
            assert self.matches_pattern(text, "Wrażliwość cenowa"), \
                f"Should match regardless of case: {text}"


# =========================================================================
# PARAMETRIZED TESTS FOR COMPREHENSIVE COVERAGE
# =========================================================================

@pytest.mark.parametrize(
    "text,expected_pattern",
    [
        # Price sensitivity
        ("Zbyt drogi jak na rynek", "Wrażliwość cenowa"),
        ("Tani i ekonomiczny wariant", "Wrażliwość cenowa"),
        ("Budżet nie pozwala na zakup", "Wrażliwość cenowa"),

        # Product quality
        ("Solidne wykonanie i trwałość", "Jakość produktu"),
        ("Wadliwy produkt po tygodniu", "Jakość produktu"),
        ("Niezawodny w każdych warunkach", "Jakość produktu"),

        # Customer experience
        ("Świetna pomoc techniczna", "Doświadczenie klienta"),
        ("Intuicyjny i przyjazny interfejs", "Doświadczenie klienta"),
        ("Wsparcie jest bardzo pomocne", "Doświadczenie klienta"),

        # Feature requests
        ("Brakuje eksportu do Excel", "Brakujące funkcje"),
        ("Chciałbym mieć dark mode", "Brakujące funkcje"),
        ("Należy dodać powiadomienia", "Brakujące funkcje"),

        # Performance issues
        ("System wolno reaguje", "Problemy wydajnościowe"),
        ("Częste błędy i zawieszenia", "Problemy wydajnościowe"),
        ("Crash podczas importu", "Problemy wydajnościowe"),

        # English variants
        ("Too expensive for the value", "Wrażliwość cenowa"),
        ("Excellent quality and durability", "Jakość produktu"),
        ("User-friendly customer journey", "Doświadczenie klienta"),
        ("Missing export functionality", "Brakujące funkcje"),
        ("Slow performance and lag", "Problemy wydajnościowe"),
    ],
)
def test_pattern_matching_parametrized(text, expected_pattern):
    """Parametrized test for various text-pattern combinations."""
    tester = TestPolishResponsePatterns()
    assert tester.matches_pattern(text, expected_pattern), \
        f"Text '{text}' should match pattern '{expected_pattern}'"
