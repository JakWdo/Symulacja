"""
Tests for Advanced Insights Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
from uuid import uuid4

from app.services.advanced_insights_service import AdvancedInsightsService


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_responses():
    """Sample focus group responses for testing"""
    return [
        {
            "persona_id": str(uuid4()),
            "age": 25,
            "location": "New York, NY",
            "gender": "Female",
            "education_level": "Bachelor's",
            "question_index": 0,
            "question": "What do you think?",
            "response": "I think this is great! Very positive about it.",
            "sentiment": 0.8,
            "response_time": "2024-01-01T10:00:00",
        },
        {
            "persona_id": str(uuid4()),
            "age": 35,
            "location": "Los Angeles, CA",
            "gender": "Male",
            "education_level": "Master's",
            "question_index": 0,
            "question": "What do you think?",
            "response": "Not impressed. Could be better.",
            "sentiment": -0.3,
            "response_time": "2024-01-01T10:01:00",
        },
        {
            "persona_id": str(uuid4()),
            "age": 45,
            "location": "Chicago, IL",
            "gender": "Female",
            "education_level": "PhD",
            "question_index": 1,
            "question": "How would you improve it?",
            "response": "Add more features and improve design.",
            "sentiment": 0.2,
            "response_time": "2024-01-01T10:02:00",
        },
    ]


class TestAdvancedInsightsService:
    """Test suite for AdvancedInsightsService"""

    @pytest.mark.asyncio
    async def test_demographic_correlations(self, mock_db, sample_responses):
        """Test demographic-sentiment correlation analysis"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'demographic_correlations' in insights
            correlations = insights['demographic_correlations']

            # Check for expected correlation keys
            assert 'age_sentiment' in correlations
            assert 'gender_sentiment' in correlations
            assert 'education_sentiment' in correlations

            # Validate structure
            for key, corr_data in correlations.items():
                if isinstance(corr_data, dict):
                    assert 'correlation' in corr_data or 'effect_size' in corr_data
                    assert 'interpretation' in corr_data

    @pytest.mark.asyncio
    async def test_behavioral_segmentation(self, mock_db, sample_responses):
        """Test behavioral segmentation with K-Means"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'behavioral_segments' in insights
            segments_data = insights['behavioral_segments']

            assert 'num_segments' in segments_data
            assert 'segments' in segments_data

            # Check segment structure
            segments = segments_data['segments']
            assert len(segments) > 0

            for segment in segments:
                assert 'label' in segment
                assert 'size' in segment
                assert 'percentage' in segment
                assert 'characteristics' in segment
                assert 'avg_sentiment' in segment['characteristics']

    @pytest.mark.asyncio
    async def test_quality_metrics(self, mock_db, sample_responses):
        """Test response quality metrics calculation"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'quality_metrics' in insights
            quality = insights['quality_metrics']

            # Check for required metrics
            assert 'overall_quality' in quality
            assert 'depth_score' in quality
            assert 'constructiveness_score' in quality
            assert 'specificity_score' in quality

            # Validate ranges (0-1)
            assert 0 <= quality['overall_quality'] <= 1
            assert 0 <= quality['depth_score'] <= 1
            assert 0 <= quality['constructiveness_score'] <= 1
            assert 0 <= quality['specificity_score'] <= 1

    @pytest.mark.asyncio
    async def test_temporal_analysis(self, mock_db, sample_responses):
        """Test temporal analysis of sentiment evolution"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'temporal_analysis' in insights
            temporal = insights['temporal_analysis']

            assert 'trend' in temporal
            assert 'momentum_shifts' in temporal

    @pytest.mark.asyncio
    async def test_outlier_detection(self, mock_db, sample_responses):
        """Test outlier detection using Z-scores"""
        # Add an outlier
        outlier_response = {
            "persona_id": str(uuid4()),
            "age": 25,
            "location": "Boston, MA",
            "gender": "Male",
            "education_level": "Bachelor's",
            "question_index": 0,
            "question": "What do you think?",
            "response": "This is absolutely terrible and awful!",
            "sentiment": -0.95,  # Strong outlier
            "response_time": "2024-01-01T10:03:00",
        }
        responses_with_outlier = sample_responses + [outlier_response]

        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=responses_with_outlier
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'outliers' in insights
            outliers = insights['outliers']

            assert 'count' in outliers
            assert 'responses' in outliers

    @pytest.mark.asyncio
    async def test_engagement_patterns(self, mock_db, sample_responses):
        """Test engagement pattern analysis"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'engagement_patterns' in insights
            engagement = insights['engagement_patterns']

            assert 'high_engagers' in engagement
            assert 'low_engagers' in engagement

    @pytest.mark.asyncio
    async def test_comparative_analysis(self, mock_db, sample_responses):
        """Test comparative question analysis"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=sample_responses
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            assert 'comparative_analysis' in insights
            comparative = insights['comparative_analysis']

            assert 'best_question' in comparative
            assert 'worst_question' in comparative

    @pytest.mark.asyncio
    async def test_empty_responses(self, mock_db):
        """Test handling of empty responses"""
        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=[]
        ):
            service = AdvancedInsightsService()

            with pytest.raises(ValueError, match="No responses found"):
                await service.generate_advanced_insights(
                    db=mock_db,
                    focus_group_id=str(uuid4())
                )

    @pytest.mark.asyncio
    async def test_insufficient_data_for_segmentation(self, mock_db):
        """Test handling of insufficient data for clustering"""
        # Only 1 response - not enough for clustering
        single_response = [{
            "persona_id": str(uuid4()),
            "age": 25,
            "location": "New York, NY",
            "gender": "Female",
            "education_level": "Bachelor's",
            "question_index": 0,
            "question": "What do you think?",
            "response": "Good.",
            "sentiment": 0.5,
            "response_time": "2024-01-01T10:00:00",
        }]

        with patch.object(
            AdvancedInsightsService,
            '_fetch_responses',
            return_value=single_response
        ):
            service = AdvancedInsightsService()
            insights = await service.generate_advanced_insights(
                db=mock_db,
                focus_group_id=str(uuid4())
            )

            # Should still return insights, but segmentation may be limited
            assert 'behavioral_segments' in insights
