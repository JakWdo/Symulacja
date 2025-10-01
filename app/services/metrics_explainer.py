"""
Metrics Explainer Service
Provides human-readable explanations for all insight metrics
Helps users understand what metrics mean and how to act on them
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetricExplanation:
    """Explanation for a single metric"""
    name: str
    value: Any
    interpretation: str  # What does this value mean?
    context: str  # Why does it matter?
    action: str  # What should you do about it?
    benchmark: Optional[str] = None  # How does it compare?


class MetricsExplainerService:
    """Generate contextual explanations for insight metrics"""

    def __init__(self):
        pass

    def explain_idea_score(self, score: float, grade: str) -> MetricExplanation:
        """Explain the overall idea score"""

        if score >= 85:
            interpretation = "Outstanding reception - participants are highly positive and aligned."
            action = "Move forward confidently. Consider expanding to broader audience testing."
            benchmark = "Top 10% of concepts tested"
        elif score >= 70:
            interpretation = "Strong positive reception with good alignment among participants."
            action = "Proceed with development. Address any minor concerns raised."
            benchmark = "Top 25% of concepts tested"
        elif score >= 55:
            interpretation = "Mixed reception - some enthusiasm but also notable concerns."
            action = "Investigate the concerns. Consider iterating on problem areas before launch."
            benchmark = "Average performance"
        elif score >= 40:
            interpretation = "Weak reception - participants have significant reservations."
            action = "Major revision needed. Re-examine core value proposition."
            benchmark = "Bottom 25% of concepts"
        else:
            interpretation = "Poor reception - concept didn't resonate with target audience."
            action = "Consider pivoting or conducting discovery research to understand needs better."
            benchmark = "Bottom 10% of concepts"

        context = (
            "Idea Score combines participant sentiment (how they feel) with consensus "
            "(how aligned they are). High scores indicate both positive feelings AND agreement, "
            "which are both critical for product-market fit."
        )

        return MetricExplanation(
            name="Idea Score",
            value=f"{score:.1f}/100 ({grade})",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_consensus(self, consensus: float) -> MetricExplanation:
        """Explain consensus metric"""

        percentage = consensus * 100

        if consensus >= 0.75:
            interpretation = "Very high agreement - participants share similar views."
            action = "You have a clear signal. Use this alignment to guide product decisions."
            benchmark = "Strong consensus"
        elif consensus >= 0.55:
            interpretation = "Moderate agreement - most participants align, with some divergence."
            action = "Identify which segments disagree and why. May need targeted messaging."
            benchmark = "Typical consensus range"
        elif consensus >= 0.40:
            interpretation = "Low agreement - participants have varying opinions."
            action = "Dig into demographic/psychographic splits. Concept may appeal to specific segments only."
            benchmark = "Polarized opinions"
        else:
            interpretation = "Very low agreement - participants have conflicting views."
            action = "Red flag. Re-examine if concept is solving a real problem or if positioning is unclear."
            benchmark = "Highly polarized"

        context = (
            "Consensus measures how similarly participants responded using semantic clustering. "
            "Low consensus doesn't always mean bad - it might indicate you need different positioning "
            "for different segments. High consensus with negative sentiment is worse than low consensus "
            "with mixed sentiment."
        )

        return MetricExplanation(
            name="Consensus",
            value=f"{percentage:.1f}%",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_sentiment(self, avg_sentiment: float, positive_ratio: float, negative_ratio: float) -> MetricExplanation:
        """Explain sentiment metrics"""

        if avg_sentiment > 0.3:
            interpretation = "Strongly positive sentiment - participants like the concept."
            action = "Amplify what's working. Use positive quotes in marketing."
        elif avg_sentiment > 0.1:
            interpretation = "Moderately positive sentiment - generally favorable reception."
            action = "Build on positive aspects while addressing any concerns."
        elif avg_sentiment > -0.1:
            interpretation = "Neutral sentiment - participants are lukewarm or uncertain."
            action = "Concept needs stronger differentiation or clearer value proposition."
        elif avg_sentiment > -0.3:
            interpretation = "Moderately negative sentiment - participants have reservations."
            action = "Identify and address key objections before proceeding."
        else:
            interpretation = "Strongly negative sentiment - participants dislike core aspects."
            action = "Major changes needed or consider alternative approaches."

        context = (
            f"Average sentiment is {avg_sentiment:+.2f} on a scale from -1 (very negative) to +1 (very positive). "
            f"{positive_ratio*100:.0f}% of responses were positive, {negative_ratio*100:.0f}% were negative. "
            "Sentiment is analyzed using both keyword matching and semantic analysis. "
            "Neutral responses might indicate confusion or lack of strong opinion."
        )

        benchmark = None
        if positive_ratio > 0.7:
            benchmark = "High positive ratio - concept resonates well"
        elif negative_ratio > 0.3:
            benchmark = "High negative ratio - significant concerns present"

        return MetricExplanation(
            name="Sentiment Analysis",
            value=f"{avg_sentiment:+.2f} avg ({positive_ratio*100:.0f}% positive)",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_completion_rate(self, completion_rate: float) -> MetricExplanation:
        """Explain completion rate"""

        percentage = completion_rate * 100

        if completion_rate >= 0.95:
            interpretation = "Excellent engagement - nearly all participants answered all questions."
            action = "Participants are invested. Their feedback is reliable."
            benchmark = "High engagement"
        elif completion_rate >= 0.80:
            interpretation = "Good engagement - most participants completed the session."
            action = "Acceptable dropout. Check if specific questions caused exits."
            benchmark = "Normal engagement"
        elif completion_rate >= 0.60:
            interpretation = "Moderate engagement - noticeable dropout during session."
            action = "Review question complexity and session length. May need to streamline."
            benchmark = "Below average engagement"
        else:
            interpretation = "Low engagement - significant dropout occurred."
            action = "Warning sign. Questions may be too complex, unclear, or session too long."
            benchmark = "Poor engagement - needs attention"

        context = (
            "Completion rate measures what percentage of expected responses were received "
            "(participants × questions). Low rates might indicate survey fatigue, confusing questions, "
            "or lack of interest in the topic."
        )

        return MetricExplanation(
            name="Completion Rate",
            value=f"{percentage:.1f}%",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_consistency_score(self, consistency_score: Optional[float]) -> MetricExplanation:
        """Explain consistency score"""

        if consistency_score is None:
            return MetricExplanation(
                name="Consistency Score",
                value="N/A",
                interpretation="Not enough data to calculate consistency.",
                context="Consistency measures how well responses align with participant backgrounds and previous answers.",
                action="Continue collecting responses to enable consistency analysis.",
                benchmark=None
            )

        if consistency_score >= 0.85:
            interpretation = "Very high consistency - responses strongly align with participant profiles."
            action = "Personas are responding authentically. Data is reliable."
            benchmark = "Excellent persona fidelity"
        elif consistency_score >= 0.70:
            interpretation = "Good consistency - most responses match expected behavior."
            action = "Acceptable quality. Minor inconsistencies won't significantly impact insights."
            benchmark = "Good persona quality"
        elif consistency_score >= 0.55:
            interpretation = "Moderate consistency - some responses deviate from profiles."
            action = "Review personas with low scores. May need better prompt engineering."
            benchmark = "Acceptable but room for improvement"
        else:
            interpretation = "Low consistency - many responses don't match participant backgrounds."
            action = "Quality issue detected. Regenerate personas or refine prompts."
            benchmark = "Quality concerns - action needed"

        context = (
            "Consistency Score measures how well synthetic persona responses align with their "
            "defined characteristics (age, background, values, etc.). This is crucial for ensuring "
            "the simulated focus group produces reliable insights. Lower scores might indicate "
            "persona definitions are too vague or prompts aren't being followed correctly."
        )

        return MetricExplanation(
            name="Consistency Score",
            value=f"{consistency_score:.2f}",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_response_time(self, avg_response_time_ms: Optional[float]) -> MetricExplanation:
        """Explain average response time"""

        if avg_response_time_ms is None:
            return MetricExplanation(
                name="Avg Response Time",
                value="N/A",
                interpretation="Response time data not available.",
                context="Response time indicates processing complexity.",
                action="Enable response time tracking for performance insights.",
                benchmark=None
            )

        seconds = avg_response_time_ms / 1000

        if seconds < 2:
            interpretation = "Very fast responses - quick generation time."
            action = "Good system performance. No bottlenecks detected."
            benchmark = "Excellent performance"
        elif seconds < 5:
            interpretation = "Fast responses - good generation time."
            action = "Normal performance range for AI-generated responses."
            benchmark = "Good performance"
        elif seconds < 10:
            interpretation = "Moderate response time - acceptable performance."
            action = "Performance is adequate but could be optimized if scaling."
            benchmark = "Average performance"
        else:
            interpretation = "Slow responses - generation is taking longer than expected."
            action = "Check API quotas, model selection, or prompt complexity. Consider optimization."
            benchmark = "Below target performance"

        context = (
            f"Average response time was {seconds:.1f} seconds per answer. "
            "This includes AI model processing, consistency checking, and data storage. "
            "Longer times might indicate complex prompts or API throttling."
        )

        return MetricExplanation(
            name="Avg Response Time",
            value=f"{avg_response_time_ms:.0f}ms ({seconds:.1f}s)",
            interpretation=interpretation,
            context=context,
            action=action,
            benchmark=benchmark
        )

    def explain_all_metrics(self, insights_data: Dict[str, Any]) -> Dict[str, MetricExplanation]:
        """Generate explanations for all metrics in insight data"""

        explanations = {}

        # Idea score
        if "idea_score" in insights_data:
            explanations["idea_score"] = self.explain_idea_score(
                insights_data["idea_score"],
                insights_data.get("idea_grade", "N/A")
            )

        metrics = insights_data.get("metrics", {})

        # Consensus
        if "consensus" in metrics:
            explanations["consensus"] = self.explain_consensus(metrics["consensus"])

        # Sentiment
        if "average_sentiment" in metrics:
            sentiment_summary = metrics.get("sentiment_summary", {})
            explanations["sentiment"] = self.explain_sentiment(
                metrics["average_sentiment"],
                sentiment_summary.get("positive_ratio", 0.0),
                sentiment_summary.get("negative_ratio", 0.0)
            )

        engagement = metrics.get("engagement", {})

        # Completion rate
        if "completion_rate" in engagement:
            explanations["completion_rate"] = self.explain_completion_rate(
                engagement["completion_rate"]
            )

        # Consistency score
        explanations["consistency_score"] = self.explain_consistency_score(
            engagement.get("consistency_score")
        )

        # Response time
        explanations["response_time"] = self.explain_response_time(
            engagement.get("average_response_time_ms")
        )

        return explanations

    def get_overall_health_assessment(self, insights_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide overall health assessment of the focus group results"""

        idea_score = insights_data.get("idea_score", 0)
        metrics = insights_data.get("metrics", {})
        consensus = metrics.get("consensus", 0)
        avg_sentiment = metrics.get("average_sentiment", 0)
        engagement = metrics.get("engagement", {})
        completion_rate = engagement.get("completion_rate", 0)
        consistency_score = engagement.get("consistency_score")

        # Calculate health score (0-100)
        health_components = []

        # Idea score contribution (40%)
        health_components.append(idea_score * 0.4)

        # Consensus contribution (20%)
        health_components.append(consensus * 100 * 0.2)

        # Engagement contribution (20%)
        health_components.append(completion_rate * 100 * 0.2)

        # Consistency contribution (20%) - if available
        if consistency_score is not None:
            health_components.append(consistency_score * 100 * 0.2)
        else:
            # If no consistency, redistribute weight
            health_components = [
                idea_score * 0.5,
                consensus * 100 * 0.25,
                completion_rate * 100 * 0.25,
            ]

        overall_health = sum(health_components)

        # Determine status
        if overall_health >= 75:
            status = "healthy"
            status_label = "Healthy"
            color = "green"
            message = "Strong results across all dimensions. Proceed with confidence."
        elif overall_health >= 60:
            status = "good"
            status_label = "Good"
            color = "blue"
            message = "Solid results with minor areas for improvement."
        elif overall_health >= 45:
            status = "fair"
            status_label = "Fair"
            color = "yellow"
            message = "Mixed results. Address concerns before moving forward."
        else:
            status = "poor"
            status_label = "Needs Attention"
            color = "red"
            message = "Significant issues detected. Major revisions recommended."

        # Identify top concerns
        concerns = []
        if idea_score < 55:
            concerns.append("Low idea score - concept needs refinement")
        if consensus < 0.5:
            concerns.append("Low consensus - polarized opinions")
        if completion_rate < 0.7:
            concerns.append("Low completion rate - engagement issues")
        if consistency_score is not None and consistency_score < 0.7:
            concerns.append("Low consistency - data quality concerns")

        return {
            "health_score": round(overall_health, 1),
            "status": status,
            "status_label": status_label,
            "color": color,
            "message": message,
            "concerns": concerns,
            "strengths": self._identify_strengths(insights_data),
        }

    def _identify_strengths(self, insights_data: Dict[str, Any]) -> List[str]:
        """Identify strengths in the results"""
        strengths = []

        idea_score = insights_data.get("idea_score", 0)
        metrics = insights_data.get("metrics", {})
        consensus = metrics.get("consensus", 0)
        sentiment_summary = metrics.get("sentiment_summary", {})
        engagement = metrics.get("engagement", {})

        if idea_score >= 70:
            strengths.append("Strong overall concept reception")
        if consensus >= 0.7:
            strengths.append("High participant alignment")
        if sentiment_summary.get("positive_ratio", 0) >= 0.65:
            strengths.append("Predominantly positive sentiment")
        if engagement.get("completion_rate", 0) >= 0.85:
            strengths.append("Excellent participant engagement")
        if engagement.get("consistency_score", 0) >= 0.8:
            strengths.append("High response quality/consistency")

        return strengths
