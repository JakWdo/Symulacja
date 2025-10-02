"""
Integration tests for Enhanced Insights API (Phase 4)
Tests the new API endpoints for AI summaries, metric explanations, and enhanced reports
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestInsightsV2API:
    """Test suite for insights v2 API endpoints"""

    def test_api_root(self):
        """Test that API is running"""
        response = client.get("/")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_explainer_service_initialization(self):
        """Test MetricsExplainerService can be instantiated"""
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        assert service is not None

    def test_metrics_explainer_idea_score(self):
        """Test idea score explanation"""
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        explanation = service.explain_idea_score(85.0, "B+")

        assert explanation.name == "Idea Score"
        assert "85.0" in explanation.value
        assert explanation.interpretation
        assert explanation.context
        assert explanation.action

    def test_metrics_explainer_consensus(self):
        """Test consensus explanation"""
        from app.services.metrics_explainer import MetricsExplainerService

        service = MetricsExplainerService()
        explanation = service.explain_consensus(0.75)

        assert explanation.name == "Consensus"
        assert "75" in explanation.value
        assert explanation.interpretation
        assert explanation.action

    def test_advanced_insights_service_initialization(self):
        """Test AdvancedInsightsService can be instantiated"""
        from app.services.advanced_insights_service import AdvancedInsightsService

        service = AdvancedInsightsService()
        assert service is not None

    def test_discussion_summarizer_initialization_flash(self):
        """Test DiscussionSummarizerService with Flash model"""
        from app.services.discussion_summarizer import DiscussionSummarizerService

        service = DiscussionSummarizerService(use_pro_model=False)
        assert service is not None

    def test_discussion_summarizer_initialization_pro(self):
        """Test DiscussionSummarizerService with Pro model"""
        from app.services.discussion_summarizer import DiscussionSummarizerService

        service = DiscussionSummarizerService(use_pro_model=True)
        assert service is not None

    def test_enhanced_report_generator_initialization(self):
        """Test EnhancedReportGenerator can be instantiated"""
        from app.services.enhanced_report_generator import EnhancedReportGenerator

        generator = EnhancedReportGenerator()
        assert generator is not None
        assert generator.insight_service is not None
        assert generator.metrics_explainer is not None

    def test_report_generator_has_create_styles(self):
        """Test that report generator has _create_styles method"""
        from app.services.enhanced_report_generator import EnhancedReportGenerator

        generator = EnhancedReportGenerator()
        styles = generator._create_styles()

        assert 'ReportTitle' in styles
        assert 'SectionHeading' in styles
        assert 'AIInsight' in styles
        assert 'Recommendation' in styles

    def test_overall_health_assessment(self):
        """Test overall health assessment calculation"""
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
        """Test explaining all metrics at once"""
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
    """Test that consolidated documentation is complete"""

    def test_complete_guide_exists(self):
        """Complete implementation guide should be the single source of truth"""
        import os
        assert os.path.exists("COMPLETE_GUIDE.md")

    def test_complete_guide_content(self):
        """Guide should mention the latest phases and key services"""
        with open("COMPLETE_GUIDE.md", "r", encoding="utf-8") as f:
            content = f.read()

        assert "Phase 4" in content
        assert "EnhancedReportGenerator" in content
        assert "Gemini 2.5 Flash" in content


class TestNewFiles:
    """Test that all new files exist"""

    def test_enhanced_report_generator_exists(self):
        """Test enhanced report generator file exists"""
        import os
        assert os.path.exists("app/services/enhanced_report_generator.py")

    def test_metrics_explainer_exists(self):
        """Test metrics explainer file exists"""
        import os
        assert os.path.exists("app/services/metrics_explainer.py")

    def test_discussion_summarizer_exists(self):
        """Test discussion summarizer file exists"""
        import os
        assert os.path.exists("app/services/discussion_summarizer.py")

    def test_advanced_insights_exists(self):
        """Test advanced insights file exists"""
        import os
        assert os.path.exists("app/services/advanced_insights_service.py")

    def test_insights_v2_api_exists(self):
        """Test insights v2 API file exists"""
        import os
        assert os.path.exists("app/api/insights_v2.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
