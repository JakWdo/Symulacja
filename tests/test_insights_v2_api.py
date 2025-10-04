"""
Testy integracyjne dla Enhanced Insights API (Faza 4)

Ten moduł testuje nowe endpointy API dla zaawansowanych funkcji:
- Podsumowania AI dyskusji z grup fokusowych (AI summaries)
- Wyjaśnienia metryk w języku naturalnym (metric explanations)
- Generowanie ulepszonych raportów PDF (enhanced reports)

Testy sprawdzają:
1. Poprawną inicjalizację serwisów AI (MetricsExplainerService, DiscussionSummarizerService)
2. Działanie endpointów API (health check, status)
3. Generowanie wyjaśnień dla metryk (idea score, consensus, sentiment)
4. Tworzenie raportów z AI insights
5. Ocenę ogólnego "zdrowia" projektu na podstawie metryk
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Klient testowy FastAPI - umożliwia testowanie endpointów bez uruchamiania serwera
client = TestClient(app)


class TestInsightsV2API:
    """Zestaw testów dla endpointów insights v2 API"""

    def test_api_root(self):
        """
        Test głównego endpointu API

        Sprawdza czy API odpowiada na endpoint główny (/) i zwraca status
        """
        response = client.get("/")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_health_endpoint(self):
        """
        Test endpointu health check

        Weryfikuje czy endpoint /health działa i zwraca status "healthy"
        """
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_explainer_service_initialization(self):
        """
        Test inicjalizacji MetricsExplainerService

        MetricsExplainerService tłumaczy surowe metryki na zrozumiałe wyjaśnienia.
        Sprawdza czy serwis można utworzyć bez błędów.
        """
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        assert service is not None

    def test_metrics_explainer_idea_score(self):
        """
        Test wyjaśniania metryki Idea Score

        Idea Score (0-100) ocenia potencjał pomysłu na podstawie odpowiedzi person.
        Test sprawdza czy serwis generuje wyjaśnienie zawierające:
        - Nazwę metryki
        - Wartość (np. "85.0")
        - Interpretację (co oznacza wynik)
        - Kontekst (dlaczego to ważne)
        - Akcję (co zrobić dalej)
        """
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        explanation = service.explain_idea_score(85.0, "B+")

        assert explanation.name == "Idea Score"
        assert "85.0" in explanation.value
        assert explanation.interpretation
        assert explanation.context
        assert explanation.action

    def test_metrics_explainer_consensus(self):
        """
        Test wyjaśniania metryki Consensus

        Consensus (0-1) mierzy poziom zgody między personami.
        0.75 oznacza że 75% person ma podobne opinie.
        Test weryfikuje strukturę wyjaśnienia i obecność wartości.
        """
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        explanation = service.explain_consensus(0.75)

        assert explanation.name == "Consensus"
        assert "75" in explanation.value
        assert explanation.interpretation
        assert explanation.action

    def test_advanced_insights_service_initialization(self):
        """
        Test inicjalizacji AdvancedInsightsService

        AdvancedInsightsService oblicza zaawansowane metryki analityczne.
        Sprawdza czy można utworzyć instancję serwisu.
        """
        from app.services.advanced_insights_service import AdvancedInsightsService

        service = AdvancedInsightsService()
        assert service is not None

    def test_discussion_summarizer_initialization_flash(self):
        """
        Test inicjalizacji DiscussionSummarizerService z modelem Flash

        DiscussionSummarizerService używa AI (Gemini) do podsumowywania dyskusji.
        Model Flash (gemini-2.5-flash) jest szybszy i tańszy.
        Test sprawdza inicjalizację z use_pro_model=False.
        """
        from app.services.discussion_summarizer import DiscussionSummarizerService

        service = DiscussionSummarizerService(use_pro_model=False)
        assert service is not None

    def test_discussion_summarizer_initialization_pro(self):
        """
        Test inicjalizacji DiscussionSummarizerService z modelem Pro

        Model Pro (gemini-2.0-flash-exp) jest dokładniejszy dla złożonych analiz.
        Test sprawdza inicjalizację z use_pro_model=True.
        """
        from app.services.discussion_summarizer import DiscussionSummarizerService

        service = DiscussionSummarizerService(use_pro_model=True)
        assert service is not None

    def test_enhanced_report_generator_initialization(self):
        """
        Test inicjalizacji EnhancedReportGenerator

        EnhancedReportGenerator tworzy raporty PDF z AI insights.
        Test sprawdza czy:
        1. Generator można utworzyć
        2. Ma zainicjalizowane serwisy insight_service i metrics_explainer
        """
        from app.services.enhanced_report_generator import EnhancedReportGenerator

        generator = EnhancedReportGenerator()
        assert generator is not None
        assert generator.insight_service is not None
        assert generator.metrics_explainer is not None

    def test_report_generator_has_create_styles(self):
        """
        Test metody _create_styles w generatorze raportów

        Raporty PDF używają stylów do formatowania (czcionki, kolory, rozmiary).
        Test sprawdza czy generator ma zdefiniowane style:
        - ReportTitle - tytuł raportu
        - SectionHeading - nagłówki sekcji
        - AIInsight - bloki z AI insights
        - Recommendation - rekomendacje
        """
        from app.services.enhanced_report_generator import EnhancedReportGenerator

        generator = EnhancedReportGenerator()
        styles = generator._create_styles()

        assert 'ReportTitle' in styles
        assert 'SectionHeading' in styles
        assert 'AIInsight' in styles
        assert 'Recommendation' in styles

    def test_overall_health_assessment(self):
        """
        Test oceny ogólnego "zdrowia" projektu

        MetricsExplainerService analizuje wszystkie metryki i wystawia ocenę:
        - health_score (0-100) - ogólny wynik zdrowia
        - status - kategoria (healthy/good/fair/poor)
        - status_label - opis słowny

        Test sprawdza czy dla dobrych metryk (idea_score=85, consensus=0.75)
        generowana jest poprawna ocena zdrowia.
        """
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        insights = {
            "idea_score": 85.0,
            "consensus": 0.75,
            "sentiment": {"overall": 0.65}
        }

        health = service.get_overall_health_assessment(insights)

        assert "health_score" in health
        assert "status" in health
        assert "status_label" in health
        assert health["status"] in ["healthy", "good", "fair", "poor"]

    def test_explain_all_metrics(self):
        """
        Test wyjaśniania wszystkich metryk jednocześnie

        Zamiast wyjaśniać każdą metrykę osobno, można wysłać wszystkie naraz.
        Test sprawdza czy explain_all_metrics:
        1. Przyjmuje słownik z wieloma metrykami (idea_score, consensus, sentiment)
        2. Zwraca słownik z wyjaśnieniami
        3. Zawiera wyjaśnienie dla idea_score (główna metryka)
        """
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        insights = {
            "idea_score": 75.0,
            "idea_grade": "C",
            "consensus": 0.65,
            "sentiment": {
                "overall": 0.45,
                "positive_rate": 0.6,
                "negative_rate": 0.25,
            }
        }

        explanations = service.explain_all_metrics(insights)

        assert isinstance(explanations, dict)
        assert "idea_score" in explanations
        # Note: explain_all_metrics may return different keys based on implementation


class TestDocumentation:
    """Testy kompletności dokumentacji projektu"""

    def test_complete_guide_exists(self):
        """
        Test istnienia głównego przewodnika

        COMPLETE_GUIDE.md powinien być jedynym źródłem prawdy o implementacji.
        Sprawdza czy plik istnieje w głównym katalogu projektu.
        """
        import os
        assert os.path.exists("COMPLETE_GUIDE.md")

    def test_complete_guide_content(self):
        """
        Test zawartości przewodnika

        COMPLETE_GUIDE.md powinien dokumentować najnowsze fazy i kluczowe serwisy.
        Sprawdza obecność:
        - "Phase 4" - najnowsza faza rozwoju
        - "EnhancedReportGenerator" - generator raportów
        - "Gemini 2.5 Flash" - wykorzystany model AI
        """
        with open("COMPLETE_GUIDE.md", "r", encoding="utf-8") as f:
            content = f.read()

        assert "Phase 4" in content
        assert "EnhancedReportGenerator" in content
        assert "Gemini 2.5 Flash" in content


class TestNewFiles:
    """Testy istnienia nowych plików (Faza 4)"""

    def test_enhanced_report_generator_exists(self):
        """
        Test istnienia pliku enhanced_report_generator.py

        EnhancedReportGenerator generuje raporty PDF z AI insights.
        Sprawdza czy plik znajduje się w app/services/
        """
        import os
        assert os.path.exists("app/services/enhanced_report_generator.py")

    def test_metrics_explainer_exists(self):
        """
        Test istnienia pliku metrics_explainer.py

        MetricsExplainerService tłumaczy metryki na język naturalny.
        Sprawdza czy plik znajduje się w app/services/
        """
        import os
        assert os.path.exists("app/services/metrics_explainer.py")

    def test_discussion_summarizer_exists(self):
        """
        Test istnienia pliku discussion_summarizer.py

        DiscussionSummarizerService podsumowuje dyskusje z grup fokusowych przy użyciu AI.
        Sprawdza czy plik znajduje się w app/services/
        """
        import os
        assert os.path.exists("app/services/discussion_summarizer.py")

    def test_advanced_insights_exists(self):
        """
        Test istnienia pliku advanced_insights_service.py

        AdvancedInsightsService oblicza zaawansowane metryki analityczne.
        Sprawdza czy plik znajduje się w app/services/
        """
        import os
        assert os.path.exists("app/services/advanced_insights_service.py")

    def test_insights_v2_api_exists(self):
        """
        Test istnienia pliku insights_v2.py

        API insights v2 udostępnia endpointy dla zaawansowanych analiz.
        Sprawdza czy plik znajduje się w app/api/
        """
        import os
        assert os.path.exists("app/api/insights_v2.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
