"""
Tests for Discussion Summarizer Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.discussion_summarizer import DiscussionSummarizerService


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_responses():
    """Sample focus group responses"""
    return [
        {
            "persona_id": str(uuid4()),
            "persona_name": "Sarah Johnson",
            "age": 28,
            "gender": "Female",
            "location": "New York, NY",
            "occupation": "Marketing Manager",
            "question": "What do you think about the product?",
            "response": "I really love the design and user interface. It's very intuitive.",
            "sentiment": 0.8,
        },
        {
            "persona_id": str(uuid4()),
            "persona_name": "Michael Chen",
            "age": 35,
            "gender": "Male",
            "location": "San Francisco, CA",
            "occupation": "Software Engineer",
            "question": "What do you think about the product?",
            "response": "The performance could be better. It's a bit slow.",
            "sentiment": -0.2,
        },
        {
            "persona_id": str(uuid4()),
            "persona_name": "Emily Davis",
            "age": 42,
            "gender": "Female",
            "location": "Chicago, IL",
            "occupation": "Business Analyst",
            "question": "How would you improve it?",
            "response": "Add more customization options and improve the speed.",
            "sentiment": 0.3,
        },
    ]


@pytest.fixture
def sample_demographics():
    """Sample demographic distribution"""
    return {
        "age_distribution": {"25-34": 2, "35-44": 1},
        "gender_distribution": {"Female": 2, "Male": 1},
        "location_distribution": {
            "New York, NY": 1,
            "San Francisco, CA": 1,
            "Chicago, IL": 1,
        },
    }


class TestDiscussionSummarizerService:
    """Test suite for DiscussionSummarizerService"""

    def test_service_initialization_flash(self):
        """Test service initialization with Flash model"""
        service = DiscussionSummarizerService(use_pro_model=False)
        assert service.use_pro_model is False

    def test_service_initialization_pro(self):
        """Test service initialization with Pro model"""
        service = DiscussionSummarizerService(use_pro_model=True)
        assert service.use_pro_model is True

    @pytest.mark.asyncio
    async def test_generate_summary_basic(self, mock_db, sample_responses):
        """Test basic summary generation"""
        mock_llm_response = {
            "executive_summary": "The focus group revealed mixed reactions to the product.",
            "key_insights": [
                "Users appreciate the design and interface",
                "Performance issues were a common concern",
                "Customization features are desired",
            ],
            "surprising_findings": [
                "Younger users were more positive than expected"
            ],
            "recommendations": [
                "Optimize performance for better user experience",
                "Add customization options in next release",
            ],
        }

        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value={}
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            return_value=mock_llm_response
        ):
            service = DiscussionSummarizerService(use_pro_model=False)
            summary = await service.generate_discussion_summary(
                db=mock_db,
                focus_group_id=str(uuid4()),
                include_demographics=False,
                include_recommendations=True,
            )

            assert "executive_summary" in summary
            assert "key_insights" in summary
            assert "recommendations" in summary
            assert isinstance(summary["key_insights"], list)
            assert len(summary["key_insights"]) > 0

    @pytest.mark.asyncio
    async def test_generate_summary_with_demographics(
        self, mock_db, sample_responses, sample_demographics
    ):
        """Test summary generation with demographics"""
        mock_llm_response = {
            "executive_summary": "Summary with demographic context.",
            "key_insights": ["Insight 1", "Insight 2"],
            "segment_analysis": [
                {
                    "segment": "Female participants (67%)",
                    "finding": "More positive about design",
                }
            ],
        }

        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value=sample_demographics
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            return_value=mock_llm_response
        ):
            service = DiscussionSummarizerService(use_pro_model=False)
            summary = await service.generate_discussion_summary(
                db=mock_db,
                focus_group_id=str(uuid4()),
                include_demographics=True,
                include_recommendations=False,
            )

            assert "segment_analysis" in summary
            assert isinstance(summary["segment_analysis"], list)

    @pytest.mark.asyncio
    async def test_generate_summary_without_recommendations(
        self, mock_db, sample_responses
    ):
        """Test summary generation without recommendations"""
        mock_llm_response = {
            "executive_summary": "Summary without recommendations.",
            "key_insights": ["Insight 1", "Insight 2"],
        }

        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value={}
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            return_value=mock_llm_response
        ):
            service = DiscussionSummarizerService(use_pro_model=False)
            summary = await service.generate_discussion_summary(
                db=mock_db,
                focus_group_id=str(uuid4()),
                include_demographics=False,
                include_recommendations=False,
            )

            # Recommendations should not be present or should be empty
            assert "recommendations" not in summary or len(summary.get("recommendations", [])) == 0

    @pytest.mark.asyncio
    async def test_empty_responses_error(self, mock_db):
        """Test error handling for empty responses"""
        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=[]
        ):
            service = DiscussionSummarizerService(use_pro_model=False)

            with pytest.raises(ValueError, match="No responses found"):
                await service.generate_discussion_summary(
                    db=mock_db,
                    focus_group_id=str(uuid4()),
                )

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, mock_db, sample_responses):
        """Test handling of LLM errors"""
        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value={}
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            side_effect=Exception("LLM API Error")
        ):
            service = DiscussionSummarizerService(use_pro_model=False)

            with pytest.raises(Exception, match="LLM API Error"):
                await service.generate_discussion_summary(
                    db=mock_db,
                    focus_group_id=str(uuid4()),
                )

    @pytest.mark.asyncio
    async def test_sentiment_narrative(self, mock_db, sample_responses):
        """Test sentiment narrative generation"""
        mock_llm_response = {
            "executive_summary": "Overall sentiment was positive.",
            "key_insights": ["Insight 1"],
            "sentiment_narrative": "Participants showed enthusiasm for design but concerns about performance.",
        }

        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value={}
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            return_value=mock_llm_response
        ):
            service = DiscussionSummarizerService(use_pro_model=False)
            summary = await service.generate_discussion_summary(
                db=mock_db,
                focus_group_id=str(uuid4()),
            )

            assert "sentiment_narrative" in summary
            assert isinstance(summary["sentiment_narrative"], str)
            assert len(summary["sentiment_narrative"]) > 0

    @pytest.mark.asyncio
    async def test_surprising_findings(self, mock_db, sample_responses):
        """Test surprising findings extraction"""
        mock_llm_response = {
            "executive_summary": "Summary",
            "key_insights": ["Insight 1"],
            "surprising_findings": [
                "Unexpected positive reaction from technical users",
                "Design was valued more than features",
            ],
        }

        with patch.object(
            DiscussionSummarizerService,
            '_fetch_responses',
            return_value=sample_responses
        ), patch.object(
            DiscussionSummarizerService,
            '_fetch_demographics',
            return_value={}
        ), patch.object(
            DiscussionSummarizerService,
            '_call_llm',
            return_value=mock_llm_response
        ):
            service = DiscussionSummarizerService(use_pro_model=False)
            summary = await service.generate_discussion_summary(
                db=mock_db,
                focus_group_id=str(uuid4()),
            )

            assert "surprising_findings" in summary
            assert isinstance(summary["surprising_findings"], list)
            assert len(summary["surprising_findings"]) == 2

    def test_format_responses_for_llm(self):
        """Test response formatting for LLM input"""
        service = DiscussionSummarizerService(use_pro_model=False)

        responses = [
            {
                "persona_name": "John Doe",
                "question": "What do you think?",
                "response": "It's great!",
                "sentiment": 0.8,
            },
            {
                "persona_name": "Jane Smith",
                "question": "Any concerns?",
                "response": "A bit expensive.",
                "sentiment": -0.3,
            },
        ]

        formatted = service._format_responses_for_llm(responses)

        assert isinstance(formatted, str)
        assert "John Doe" in formatted
        assert "Jane Smith" in formatted
        assert "It's great!" in formatted
        assert "A bit expensive" in formatted

    def test_format_demographics_for_llm(self):
        """Test demographics formatting for LLM input"""
        service = DiscussionSummarizerService(use_pro_model=False)

        demographics = {
            "age_distribution": {"25-34": 5, "35-44": 3},
            "gender_distribution": {"Male": 4, "Female": 4},
        }

        formatted = service._format_demographics_for_llm(demographics)

        assert isinstance(formatted, str)
        assert "25-34" in formatted
        assert "Male" in formatted
        assert "Female" in formatted
