"""
Tests for Enhanced Report Generator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.enhanced_report_generator import EnhancedReportGenerator
from app.models import FocusGroup, Project


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def mock_focus_group():
    """Mock focus group"""
    fg = MagicMock(spec=FocusGroup)
    fg.id = uuid4()
    fg.name = "Test Focus Group"
    fg.project_id = uuid4()
    fg.persona_ids = [str(uuid4()) for _ in range(5)]
    fg.questions = ["Question 1?", "Question 2?", "Question 3?"]
    fg.status = "completed"
    fg.created_at = datetime.now()
    return fg


@pytest.fixture
def mock_project():
    """Mock project"""
    proj = MagicMock(spec=Project)
    proj.id = uuid4()
    proj.name = "Test Product Research"
    proj.description = "Market research for new product launch"
    return proj


@pytest.fixture
def sample_insights():
    """Sample insights data"""
    return {
        "idea_score": 85.5,
        "idea_grade": "B+",
        "consensus": 0.72,
        "sentiment": {
            "overall": 0.55,
            "positive_rate": 0.65,
            "negative_rate": 0.2,
            "neutral_rate": 0.15,
        },
        "diversity": 0.58,
        "response_quality": {
            "avg_length": 125,
            "participation_rate": 0.92,
        },
    }


@pytest.fixture
def sample_ai_summary():
    """Sample AI summary"""
    return {
        "executive_summary": "The focus group showed positive reception overall with some concerns about pricing and features.",
        "key_insights": [
            "Strong appreciation for user interface design",
            "Performance concerns from technical users",
            "Price sensitivity among budget-conscious segments",
            "High demand for mobile app version",
            "Integration with existing tools is critical",
        ],
        "surprising_findings": [
            "Younger users valued data privacy more than expected",
            "Enterprise features were requested by SMB segment",
        ],
        "recommendations": [
            "Optimize performance for technical user segment",
            "Introduce tiered pricing to address sensitivity",
            "Prioritize mobile app in product roadmap",
            "Enhance data security messaging",
        ],
        "sentiment_narrative": "Overall sentiment was positive (0.55) with 65% positive responses. Design excellence drove enthusiasm while performance and pricing created some hesitation.",
    }


@pytest.fixture
def sample_advanced_insights():
    """Sample advanced insights"""
    return {
        "demographic_correlations": {
            "age_sentiment": {
                "correlation": 0.32,
                "p_value": 0.045,
                "interpretation": "Weak positive correlation - older participants slightly more positive",
            },
            "gender_sentiment": {
                "effect_size": 0.15,
                "interpretation": "Minimal gender difference in sentiment",
            },
        },
        "behavioral_segments": {
            "num_segments": 3,
            "segments": [
                {
                    "label": "Enthusiastic Contributors",
                    "size": 8,
                    "percentage": 40.0,
                    "characteristics": {
                        "avg_sentiment": 0.75,
                        "avg_response_length": 180,
                    },
                },
                {
                    "label": "Pragmatic Skeptics",
                    "size": 7,
                    "percentage": 35.0,
                    "characteristics": {
                        "avg_sentiment": 0.25,
                        "avg_response_length": 140,
                    },
                },
                {
                    "label": "Neutral Observers",
                    "size": 5,
                    "percentage": 25.0,
                    "characteristics": {
                        "avg_sentiment": 0.0,
                        "avg_response_length": 95,
                    },
                },
            ],
        },
        "quality_metrics": {
            "overall_quality": 0.78,
            "depth_score": 0.72,
            "constructiveness_score": 0.81,
            "specificity_score": 0.75,
        },
    }


class TestEnhancedReportGenerator:
    """Test suite for EnhancedReportGenerator"""

    @pytest.mark.asyncio
    async def test_generate_basic_report(
        self, mock_db, mock_focus_group, mock_project, sample_insights
    ):
        """Test basic report generation without AI summary or advanced insights"""
        with patch("app.services.enhanced_report_generator.select") as mock_select, \
             patch.object(
                 EnhancedReportGenerator,
                 "__init__",
                 return_value=None
             ):

            # Mock database queries
            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_focus_group,
                mock_project,
            ]

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.insight_service.generate_focus_group_insights = AsyncMock(
                return_value=sample_insights
            )
            generator.metrics_explainer = MagicMock()
            generator.metrics_explainer.explain_all_metrics.return_value = {}
            generator.metrics_explainer.get_overall_health_assessment.return_value = {
                "health_score": 75.0,
                "status": "good",
                "status_label": "Good Performance",
            }

            pdf_bytes = await generator.generate_enhanced_pdf_report(
                db=mock_db,
                focus_group_id=mock_focus_group.id,
                include_ai_summary=False,
                include_advanced_insights=False,
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            # PDF files start with %PDF
            assert pdf_bytes[:4] == b'%PDF'

    @pytest.mark.asyncio
    async def test_generate_report_with_ai_summary(
        self, mock_db, mock_focus_group, mock_project, sample_insights, sample_ai_summary
    ):
        """Test report generation with AI summary"""
        with patch("app.services.enhanced_report_generator.select"), \
             patch("app.services.enhanced_report_generator.DiscussionSummarizerService") as mock_summarizer_class, \
             patch.object(EnhancedReportGenerator, "__init__", return_value=None):

            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_focus_group,
                mock_project,
            ]

            # Mock AI summarizer
            mock_summarizer = MagicMock()
            mock_summarizer.generate_discussion_summary = AsyncMock(
                return_value=sample_ai_summary
            )
            mock_summarizer_class.return_value = mock_summarizer

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.insight_service.generate_focus_group_insights = AsyncMock(
                return_value=sample_insights
            )
            generator.metrics_explainer = MagicMock()
            generator.metrics_explainer.explain_all_metrics.return_value = {}
            generator.metrics_explainer.get_overall_health_assessment.return_value = {
                "health_score": 75.0,
                "status": "good",
                "status_label": "Good Performance",
            }

            pdf_bytes = await generator.generate_enhanced_pdf_report(
                db=mock_db,
                focus_group_id=mock_focus_group.id,
                include_ai_summary=True,
                use_pro_model=False,
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            mock_summarizer.generate_discussion_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_report_with_advanced_insights(
        self, mock_db, mock_focus_group, mock_project, sample_insights, sample_advanced_insights
    ):
        """Test report generation with advanced insights"""
        with patch("app.services.enhanced_report_generator.select"), \
             patch("app.services.enhanced_report_generator.AdvancedInsightsService") as mock_advanced_class, \
             patch.object(EnhancedReportGenerator, "__init__", return_value=None):

            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_focus_group,
                mock_project,
            ]

            # Mock advanced insights service
            mock_advanced = MagicMock()
            mock_advanced.generate_advanced_insights = AsyncMock(
                return_value=sample_advanced_insights
            )
            mock_advanced_class.return_value = mock_advanced

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.insight_service.generate_focus_group_insights = AsyncMock(
                return_value=sample_insights
            )
            generator.metrics_explainer = MagicMock()
            generator.metrics_explainer.explain_all_metrics.return_value = {}
            generator.metrics_explainer.get_overall_health_assessment.return_value = {
                "health_score": 75.0,
                "status": "good",
                "status_label": "Good Performance",
            }

            pdf_bytes = await generator.generate_enhanced_pdf_report(
                db=mock_db,
                focus_group_id=mock_focus_group.id,
                include_advanced_insights=True,
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            mock_advanced.generate_advanced_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_full_report(
        self,
        mock_db,
        mock_focus_group,
        mock_project,
        sample_insights,
        sample_ai_summary,
        sample_advanced_insights,
    ):
        """Test full report generation with all features"""
        with patch("app.services.enhanced_report_generator.select"), \
             patch("app.services.enhanced_report_generator.DiscussionSummarizerService") as mock_summarizer_class, \
             patch("app.services.enhanced_report_generator.AdvancedInsightsService") as mock_advanced_class, \
             patch.object(EnhancedReportGenerator, "__init__", return_value=None):

            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_focus_group,
                mock_project,
            ]

            # Mock services
            mock_summarizer = MagicMock()
            mock_summarizer.generate_discussion_summary = AsyncMock(
                return_value=sample_ai_summary
            )
            mock_summarizer_class.return_value = mock_summarizer

            mock_advanced = MagicMock()
            mock_advanced.generate_advanced_insights = AsyncMock(
                return_value=sample_advanced_insights
            )
            mock_advanced_class.return_value = mock_advanced

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.insight_service.generate_focus_group_insights = AsyncMock(
                return_value=sample_insights
            )
            generator.metrics_explainer = MagicMock()
            generator.metrics_explainer.explain_all_metrics.return_value = {}
            generator.metrics_explainer.get_overall_health_assessment.return_value = {
                "health_score": 75.0,
                "status": "good",
                "status_label": "Good Performance",
            }

            pdf_bytes = await generator.generate_enhanced_pdf_report(
                db=mock_db,
                focus_group_id=mock_focus_group.id,
                include_ai_summary=True,
                include_advanced_insights=True,
                use_pro_model=True,
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
            mock_summarizer.generate_discussion_summary.assert_called_once()
            mock_advanced.generate_advanced_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_focus_group_not_found(self, mock_db):
        """Test error handling when focus group is not found"""
        with patch("app.services.enhanced_report_generator.select"), \
             patch.object(EnhancedReportGenerator, "__init__", return_value=None):

            mock_db.execute.return_value.scalar_one_or_none.return_value = None

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.metrics_explainer = MagicMock()

            with pytest.raises(ValueError, match="Focus group not found"):
                await generator.generate_enhanced_pdf_report(
                    db=mock_db,
                    focus_group_id=uuid4(),
                )

    @pytest.mark.asyncio
    async def test_ai_summary_failure_graceful(
        self, mock_db, mock_focus_group, mock_project, sample_insights
    ):
        """Test that report generation continues even if AI summary fails"""
        with patch("app.services.enhanced_report_generator.select"), \
             patch("app.services.enhanced_report_generator.DiscussionSummarizerService") as mock_summarizer_class, \
             patch.object(EnhancedReportGenerator, "__init__", return_value=None):

            mock_db.execute.return_value.scalar_one_or_none.side_effect = [
                mock_focus_group,
                mock_project,
            ]

            # Mock AI summarizer to fail
            mock_summarizer = MagicMock()
            mock_summarizer.generate_discussion_summary = AsyncMock(
                side_effect=Exception("LLM API Error")
            )
            mock_summarizer_class.return_value = mock_summarizer

            generator = EnhancedReportGenerator()
            generator.insight_service = MagicMock()
            generator.insight_service.generate_focus_group_insights = AsyncMock(
                return_value=sample_insights
            )
            generator.metrics_explainer = MagicMock()
            generator.metrics_explainer.explain_all_metrics.return_value = {}
            generator.metrics_explainer.get_overall_health_assessment.return_value = {
                "health_score": 75.0,
                "status": "good",
                "status_label": "Good Performance",
            }

            # Should still generate report without AI summary
            pdf_bytes = await generator.generate_enhanced_pdf_report(
                db=mock_db,
                focus_group_id=mock_focus_group.id,
                include_ai_summary=True,
            )

            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
