"""
Tests for Metrics Explainer Service
"""

import pytest
from app.services.metrics_explainer import MetricsExplainerService, MetricExplanation


class TestMetricsExplainerService:
    """Test suite for MetricsExplainerService"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return MetricsExplainerService()

    @pytest.fixture
    def sample_insights(self):
        """Sample insights data for testing"""
        return {
            "idea_score": 85.5,
            "idea_grade": "B+",
            "consensus": 0.75,
            "sentiment": {
                "overall": 0.65,
                "positive_rate": 0.7,
                "negative_rate": 0.15,
                "neutral_rate": 0.15,
            },
            "diversity": 0.6,
            "response_quality": {
                "avg_length": 120,
                "participation_rate": 0.95,
            }
        }

    def test_explain_idea_score_excellent(self, service):
        """Test explanation for excellent idea score (A grade)"""
        explanation = service.explain_idea_score(92.0, "A")

        assert isinstance(explanation, MetricExplanation)
        assert explanation.name == "Idea Score"
        assert "92.0" in explanation.value
        assert "Grade: A" in explanation.value
        assert "excellent" in explanation.interpretation.lower()
        assert explanation.benchmark is not None

    def test_explain_idea_score_good(self, service):
        """Test explanation for good idea score (B grade)"""
        explanation = service.explain_idea_score(85.0, "B+")

        assert "85.0" in explanation.value
        assert "Grade: B+" in explanation.value
        assert "strong" in explanation.interpretation.lower() or "good" in explanation.interpretation.lower()

    def test_explain_idea_score_fair(self, service):
        """Test explanation for fair idea score (C grade)"""
        explanation = service.explain_idea_score(72.0, "C")

        assert "72.0" in explanation.value
        assert "Grade: C" in explanation.value
        assert "room for improvement" in explanation.interpretation.lower() or "moderate" in explanation.interpretation.lower()

    def test_explain_idea_score_poor(self, service):
        """Test explanation for poor idea score (D grade)"""
        explanation = service.explain_idea_score(55.0, "D")

        assert "55.0" in explanation.value
        assert "Grade: D" in explanation.value
        assert "concerning" in explanation.interpretation.lower() or "weak" in explanation.interpretation.lower()

    def test_explain_consensus_high(self, service):
        """Test explanation for high consensus"""
        explanation = service.explain_consensus(0.85)

        assert isinstance(explanation, MetricExplanation)
        assert explanation.name == "Consensus Level"
        assert "85.0%" in explanation.value
        assert "strong agreement" in explanation.interpretation.lower()
        assert "healthy" in explanation.context.lower()

    def test_explain_consensus_moderate(self, service):
        """Test explanation for moderate consensus"""
        explanation = service.explain_consensus(0.65)

        assert "65.0%" in explanation.value
        assert "moderate" in explanation.interpretation.lower()

    def test_explain_consensus_low(self, service):
        """Test explanation for low consensus"""
        explanation = service.explain_consensus(0.40)

        assert "40.0%" in explanation.value
        assert "significant disagreement" in explanation.interpretation.lower() or "low" in explanation.interpretation.lower()

    def test_explain_consensus_very_low(self, service):
        """Test explanation for very low consensus"""
        explanation = service.explain_consensus(0.25)

        assert "25.0%" in explanation.value
        assert "critical" in explanation.interpretation.lower() or "major disagreement" in explanation.interpretation.lower()

    def test_explain_sentiment_very_positive(self, service):
        """Test explanation for very positive sentiment"""
        sentiment_data = {
            "overall": 0.85,
            "positive_rate": 0.9,
            "negative_rate": 0.05,
            "neutral_rate": 0.05,
        }
        explanation = service.explain_sentiment(sentiment_data)

        assert isinstance(explanation, MetricExplanation)
        assert explanation.name == "Overall Sentiment"
        assert "0.85" in explanation.value
        assert "very positive" in explanation.interpretation.lower() or "highly positive" in explanation.interpretation.lower()

    def test_explain_sentiment_positive(self, service):
        """Test explanation for positive sentiment"""
        sentiment_data = {
            "overall": 0.55,
            "positive_rate": 0.65,
            "negative_rate": 0.2,
            "neutral_rate": 0.15,
        }
        explanation = service.explain_sentiment(sentiment_data)

        assert "0.55" in explanation.value
        assert "positive" in explanation.interpretation.lower()

    def test_explain_sentiment_neutral(self, service):
        """Test explanation for neutral sentiment"""
        sentiment_data = {
            "overall": 0.15,
            "positive_rate": 0.35,
            "negative_rate": 0.3,
            "neutral_rate": 0.35,
        }
        explanation = service.explain_sentiment(sentiment_data)

        assert "0.15" in explanation.value
        assert "mixed" in explanation.interpretation.lower() or "neutral" in explanation.interpretation.lower()

    def test_explain_sentiment_negative(self, service):
        """Test explanation for negative sentiment"""
        sentiment_data = {
            "overall": -0.45,
            "positive_rate": 0.2,
            "negative_rate": 0.7,
            "neutral_rate": 0.1,
        }
        explanation = service.explain_sentiment(sentiment_data)

        assert "-0.45" in explanation.value
        assert "negative" in explanation.interpretation.lower()

    def test_explain_all_metrics(self, service, sample_insights):
        """Test explaining all metrics at once"""
        explanations = service.explain_all_metrics(sample_insights)

        assert isinstance(explanations, dict)
        assert "idea_score" in explanations
        assert "consensus" in explanations
        assert "sentiment" in explanations

        # Validate all are MetricExplanation instances
        for key, exp in explanations.items():
            assert isinstance(exp, MetricExplanation)
            assert exp.name
            assert exp.value
            assert exp.interpretation
            assert exp.context
            assert exp.action

    def test_overall_health_assessment_healthy(self, service):
        """Test health assessment for healthy metrics"""
        insights = {
            "idea_score": 90.0,
            "consensus": 0.80,
            "sentiment": {"overall": 0.75},
        }

        health = service.get_overall_health_assessment(insights)

        assert health["health_score"] >= 80
        assert health["status"] == "healthy"
        assert "Excellent" in health["status_label"] or "Strong" in health["status_label"]
        assert len(health["strengths"]) > 0

    def test_overall_health_assessment_good(self, service):
        """Test health assessment for good metrics"""
        insights = {
            "idea_score": 78.0,
            "consensus": 0.68,
            "sentiment": {"overall": 0.55},
        }

        health = service.get_overall_health_assessment(insights)

        assert 60 <= health["health_score"] < 80
        assert health["status"] == "good"
        assert "Good" in health["status_label"]

    def test_overall_health_assessment_fair(self, service):
        """Test health assessment for fair metrics"""
        insights = {
            "idea_score": 65.0,
            "consensus": 0.52,
            "sentiment": {"overall": 0.25},
        }

        health = service.get_overall_health_assessment(insights)

        assert 40 <= health["health_score"] < 60
        assert health["status"] == "fair"
        assert "Fair" in health["status_label"]
        assert len(health["concerns"]) > 0

    def test_overall_health_assessment_poor(self, service):
        """Test health assessment for poor metrics"""
        insights = {
            "idea_score": 52.0,
            "consensus": 0.35,
            "sentiment": {"overall": -0.25},
        }

        health = service.get_overall_health_assessment(insights)

        assert health["health_score"] < 40
        assert health["status"] == "poor"
        assert "Poor" in health["status_label"]
        assert len(health["concerns"]) > 0

    def test_metric_explanation_structure(self, service):
        """Test that all explanations have required fields"""
        explanation = service.explain_idea_score(85.0, "B+")

        # Check all required fields are present and non-empty
        assert explanation.name
        assert explanation.value
        assert explanation.interpretation
        assert explanation.context
        assert explanation.action
        # Benchmark can be None for some metrics

    def test_missing_sentiment_data(self, service):
        """Test handling of missing sentiment data"""
        insights = {
            "idea_score": 75.0,
            "consensus": 0.65,
            # sentiment missing
        }

        explanations = service.explain_all_metrics(insights)

        # Should still work, just skip sentiment
        assert "idea_score" in explanations
        assert "consensus" in explanations

    def test_edge_case_zero_consensus(self, service):
        """Test explanation for zero consensus (edge case)"""
        explanation = service.explain_consensus(0.0)

        assert "0.0%" in explanation.value
        assert explanation.interpretation  # Should still have interpretation

    def test_edge_case_perfect_consensus(self, service):
        """Test explanation for perfect consensus (edge case)"""
        explanation = service.explain_consensus(1.0)

        assert "100.0%" in explanation.value
        assert "unanimous" in explanation.interpretation.lower() or "complete agreement" in explanation.interpretation.lower()
