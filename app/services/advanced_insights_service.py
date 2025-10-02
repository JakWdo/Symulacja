"""
Advanced Insights Service
Provides deep analytics: correlations, segmentation, temporal analysis, quality metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from datetime import datetime
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FocusGroup, PersonaResponse, Persona
from app.services.insight_service import InsightService


class AdvancedInsightsService:
    """
    Generate advanced analytics for focus group discussions
    - Demographic-sentiment correlations
    - Temporal analysis (sentiment evolution)
    - Behavioral segmentation
    - Response quality metrics
    """

    def __init__(self):
        self.insight_service = InsightService()

    async def generate_advanced_insights(
        self, db: AsyncSession, focus_group_id: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive advanced insights

        Returns:
            {
                "demographic_correlations": {...},
                "temporal_analysis": {...},
                "behavioral_segments": {...},
                "quality_metrics": {...},
                "comparative_analysis": {...}
            }
        """
        # Fetch data
        focus_group = await self._get_focus_group(db, focus_group_id)
        responses = await self._get_responses(db, focus_group_id)
        personas = await self._get_personas(db, [str(r.persona_id) for r in responses])

        if not responses or not personas:
            return self._empty_advanced_insights(focus_group_id)

        # Build DataFrame for analysis
        df = self._build_analysis_dataframe(responses, personas)

        # Generate insights
        return {
            "focus_group_id": focus_group_id,
            "demographic_correlations": self._analyze_demographic_correlations(df),
            "temporal_analysis": self._analyze_temporal_patterns(df, focus_group),
            "behavioral_segments": self._analyze_behavioral_segmentation(df),
            "quality_metrics": self._analyze_response_quality(df, responses),
            "comparative_analysis": self._analyze_question_comparison(df),
            "outlier_detection": self._detect_outliers(df),
            "engagement_patterns": self._analyze_engagement_patterns(df),
        }

    def _build_analysis_dataframe(
        self, responses: List[PersonaResponse], personas: Dict[str, Persona]
    ) -> pd.DataFrame:
        """Build pandas DataFrame for advanced analysis"""
        records = []

        for response in responses:
            persona = personas.get(str(response.persona_id))
            if not persona:
                continue

            sentiment = self.insight_service.sentiment_score(response.response)

            records.append({
                # Response data
                "response_id": str(response.id),
                "persona_id": str(response.persona_id),
                "question": response.question,
                "response_text": response.response,
                "sentiment": sentiment,
                "response_length": len(response.response),
                "word_count": len(response.response.split()),
                "response_time_ms": response.response_time_ms or 0,
                "consistency_score": response.consistency_score or 0,
                "created_at": response.created_at,

                # Persona demographics
                "age": persona.age,
                "gender": persona.gender,
                "education": persona.education_level or "Unknown",
                "income": persona.income_bracket or "Unknown",
                "occupation": persona.occupation or "Unknown",
                "location": persona.location or "Unknown",

                # Persona psychology
                "openness": persona.openness or 0.5,
                "conscientiousness": persona.conscientiousness or 0.5,
                "extraversion": persona.extraversion or 0.5,
                "agreeableness": persona.agreeableness or 0.5,
                "neuroticism": persona.neuroticism or 0.5,
            })

        return pd.DataFrame(records)

    def _analyze_demographic_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze correlations between demographics and sentiment

        Returns correlations, statistical significance, and segment performance
        """
        if df.empty:
            return {}

        correlations = {}

        # Age vs Sentiment
        if "age" in df.columns and "sentiment" in df.columns:
            age_sentiment_corr, age_p_value = stats.pearsonr(df["age"], df["sentiment"])
            correlations["age_sentiment"] = {
                "correlation": float(age_sentiment_corr),
                "p_value": float(age_p_value),
                "significant": bool(age_p_value < 0.05),
                "interpretation": self._interpret_correlation(age_sentiment_corr, age_p_value, "age", "sentiment"),
            }

        # Gender vs Sentiment
        gender_groups = df.groupby("gender")["sentiment"].agg(["mean", "std", "count"])
        if len(gender_groups) > 1:
            gender_means = gender_groups["mean"].to_dict()
            gender_sentiment_data = [df[df["gender"] == g]["sentiment"].values for g in df["gender"].unique()]

            # ANOVA for multiple groups
            if len(gender_sentiment_data) > 1:
                f_stat, gender_p_value = stats.f_oneway(*gender_sentiment_data)
                correlations["gender_sentiment"] = {
                    "mean_by_gender": {str(k): float(v) for k, v in gender_means.items()},
                    "f_statistic": float(f_stat),
                    "p_value": float(gender_p_value),
                    "significant": bool(gender_p_value < 0.05),
                    "interpretation": self._interpret_group_difference(gender_means, gender_p_value, "gender"),
                }

        # Education vs Sentiment
        education_groups = df.groupby("education")["sentiment"].agg(["mean", "std", "count"])
        if len(education_groups) > 1:
            education_means = education_groups["mean"].to_dict()
            correlations["education_sentiment"] = {
                "mean_by_education": {str(k): float(v) for k, v in education_means.items()},
                "top_segment": max(education_means.items(), key=lambda x: x[1])[0] if education_means else None,
                "bottom_segment": min(education_means.items(), key=lambda x: x[1])[0] if education_means else None,
            }

        # Personality traits vs Sentiment
        personality_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        trait_correlations = {}

        for trait in personality_traits:
            if trait in df.columns:
                trait_corr, trait_p = stats.pearsonr(df[trait], df["sentiment"])
                if abs(trait_corr) > 0.2:  # Only report meaningful correlations
                    trait_correlations[trait] = {
                        "correlation": float(trait_corr),
                        "p_value": float(trait_p),
                        "significant": bool(trait_p < 0.05),
                    }

        if trait_correlations:
            correlations["personality_sentiment"] = trait_correlations

        return correlations

    def _analyze_temporal_patterns(
        self, df: pd.DataFrame, focus_group: FocusGroup
    ) -> Dict[str, Any]:
        """
        Analyze how sentiment and engagement evolved over time

        Returns temporal trends, fatigue detection, momentum shifts
        """
        if df.empty or "created_at" not in df.columns:
            return {}

        # Sort by time
        df_sorted = df.sort_values("created_at")

        # Calculate rolling sentiment
        window_size = min(10, len(df_sorted) // 3)
        if window_size < 2:
            window_size = 2

        df_sorted["sentiment_rolling"] = df_sorted["sentiment"].rolling(
            window=window_size, min_periods=1
        ).mean()

        # Detect trend
        time_index = np.arange(len(df_sorted))
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            time_index, df_sorted["sentiment"]
        )

        # Identify momentum shifts (large changes in sentiment)
        df_sorted["sentiment_change"] = df_sorted["sentiment"].diff()
        significant_shifts = df_sorted[abs(df_sorted["sentiment_change"]) > 0.3]

        # Fatigue detection (response quality declining over time)
        response_lengths = df_sorted["response_length"].values
        if len(response_lengths) > 5:
            length_trend_slope, _, _, length_p, _ = stats.linregress(
                time_index, response_lengths
            )
            fatigue_detected = bool(length_trend_slope < -5 and length_p < 0.05)
        else:
            fatigue_detected = False

        return {
            "overall_trend": {
                "slope": float(slope),
                "direction": "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable",
                "r_squared": float(r_value ** 2),
                "p_value": float(p_value),
                "significant": bool(p_value < 0.05),
            },
            "sentiment_trajectory": {
                "initial_sentiment": float(df_sorted["sentiment"].iloc[0]),
                "final_sentiment": float(df_sorted["sentiment"].iloc[-1]),
                "peak_sentiment": float(df_sorted["sentiment"].max()),
                "trough_sentiment": float(df_sorted["sentiment"].min()),
                "volatility": float(df_sorted["sentiment"].std()),
            },
            "momentum_shifts": [
                {
                    "index": int(idx),
                    "sentiment_change": float(row["sentiment_change"]),
                    "question": row["question"],
                }
                for idx, row in significant_shifts.iterrows()
            ][:5],  # Top 5 shifts
            "fatigue_analysis": {
                "fatigue_detected": fatigue_detected,
                "response_length_trend": float(length_trend_slope) if len(response_lengths) > 5 else 0,
                "interpretation": (
                    "Participants show signs of fatigue - responses getting shorter over time"
                    if fatigue_detected
                    else "No significant fatigue detected"
                ),
            },
        }

    def _analyze_behavioral_segmentation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Segment participants based on behavior patterns using clustering

        Returns behavioral segments with characteristics
        """
        if df.empty or len(df) < 10:
            return {}

        # Features for clustering
        persona_features = df.groupby("persona_id").agg({
            "sentiment": ["mean", "std"],
            "response_length": ["mean", "std"],
            "word_count": "mean",
            "consistency_score": "mean",
        }).reset_index()

        persona_features.columns = [
            "_".join(col).strip("_") for col in persona_features.columns.values
        ]

        # Normalize features
        feature_cols = [c for c in persona_features.columns if c != "persona_id"]
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(persona_features[feature_cols])

        # Determine optimal number of clusters (2-5)
        optimal_k = self._find_optimal_clusters_elbow(features_scaled, max_k=min(5, len(persona_features) // 2))

        # K-Means clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        persona_features["cluster"] = kmeans.fit_predict(features_scaled)

        # Analyze each cluster
        segments = []
        for cluster_id in range(optimal_k):
            cluster_personas = persona_features[persona_features["cluster"] == cluster_id]["persona_id"].values
            cluster_data = df[df["persona_id"].isin(cluster_personas)]

            segment = {
                "segment_id": int(cluster_id),
                "size": int(len(cluster_personas)),
                "percentage": float(len(cluster_personas) / len(persona_features) * 100),
                "characteristics": {
                    "avg_sentiment": float(cluster_data["sentiment"].mean()),
                    "sentiment_volatility": float(cluster_data["sentiment"].std()),
                    "avg_response_length": float(cluster_data["response_length"].mean()),
                    "avg_consistency": float(cluster_data["consistency_score"].mean()),
                },
                "demographics": {
                    "avg_age": float(cluster_data["age"].mean()),
                    "gender_distribution": cluster_data["gender"].value_counts().to_dict(),
                    "top_education": cluster_data["education"].mode()[0] if not cluster_data["education"].mode().empty else "Unknown",
                },
                "label": self._label_segment(cluster_data),
            }
            segments.append(segment)

        # Sort by size
        segments.sort(key=lambda x: x["size"], reverse=True)

        return {
            "num_segments": optimal_k,
            "segments": segments,
            "segmentation_quality": float(kmeans.inertia_),  # Lower is better
        }

    def _analyze_response_quality(
        self, df: pd.DataFrame, responses: List[PersonaResponse]
    ) -> Dict[str, Any]:
        """
        Analyze quality of responses beyond simple metrics

        Metrics: depth, constructiveness, specificity, coherence
        """
        if df.empty:
            return {}

        quality_scores = {
            "depth_score": self._calculate_depth_score(df),
            "constructiveness_score": self._calculate_constructiveness_score(responses),
            "specificity_score": self._calculate_specificity_score(df),
            "overall_quality": 0.0,
        }

        # Overall quality (weighted average)
        quality_scores["overall_quality"] = (
            quality_scores["depth_score"] * 0.4
            + quality_scores["constructiveness_score"] * 0.3
            + quality_scores["specificity_score"] * 0.3
        )

        # Quality distribution
        quality_scores["quality_distribution"] = {
            "high_quality_responses": int(df[df["word_count"] > 30].shape[0]),
            "medium_quality_responses": int(df[(df["word_count"] >= 15) & (df["word_count"] <= 30)].shape[0]),
            "low_quality_responses": int(df[df["word_count"] < 15].shape[0]),
        }

        return quality_scores

    def _analyze_question_comparison(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare performance across different questions

        Identifies best/worst performing questions
        """
        if df.empty:
            return {}

        question_stats = df.groupby("question").agg({
            "sentiment": ["mean", "std"],
            "response_length": "mean",
            "word_count": "mean",
            "consistency_score": "mean",
        }).reset_index()

        question_stats.columns = ["_".join(col).strip("_") for col in question_stats.columns.values]

        # Sort by sentiment
        question_stats = question_stats.sort_values("sentiment_mean", ascending=False)

        return {
            "best_questions": [
                {
                    "question": row["question"],
                    "avg_sentiment": float(row["sentiment_mean"]),
                    "avg_length": float(row["response_length_mean"]),
                }
                for _, row in question_stats.head(3).iterrows()
            ],
            "worst_questions": [
                {
                    "question": row["question"],
                    "avg_sentiment": float(row["sentiment_mean"]),
                    "avg_length": float(row["response_length_mean"]),
                }
                for _, row in question_stats.tail(3).iterrows()
            ],
            "most_polarizing": [
                {
                    "question": row["question"],
                    "sentiment_std": float(row["sentiment_std"]),
                    "avg_sentiment": float(row["sentiment_mean"]),
                }
                for _, row in question_stats.sort_values("sentiment_std", ascending=False).head(3).iterrows()
            ],
        }

    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outlier responses using statistical methods"""
        if df.empty:
            return {}

        # Z-score based outlier detection
        df["sentiment_zscore"] = np.abs(stats.zscore(df["sentiment"]))
        df["length_zscore"] = np.abs(stats.zscore(df["response_length"]))

        # Outliers are responses with z-score > 2.5
        sentiment_outliers = df[df["sentiment_zscore"] > 2.5]
        length_outliers = df[df["length_zscore"] > 2.5]

        return {
            "sentiment_outliers": int(len(sentiment_outliers)),
            "length_outliers": int(len(length_outliers)),
            "outlier_personas": list(set(sentiment_outliers["persona_id"].unique()) | set(length_outliers["persona_id"].unique())),
        }

    def _analyze_engagement_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze engagement patterns across participants"""
        if df.empty:
            return {}

        persona_engagement = df.groupby("persona_id").agg({
            "response_id": "count",
            "response_time_ms": "mean",
            "word_count": "mean",
        }).reset_index()

        persona_engagement.columns = ["persona_id", "response_count", "avg_response_time", "avg_word_count"]

        return {
            "high_engagers": int((persona_engagement["response_count"] > persona_engagement["response_count"].median()).sum()),
            "low_engagers": int((persona_engagement["response_count"] <= persona_engagement["response_count"].median()).sum()),
            "avg_response_time": float(persona_engagement["avg_response_time"].mean()),
            "avg_words_per_response": float(persona_engagement["avg_word_count"].mean()),
        }

    # ==================== Helper Methods ====================

    def _calculate_depth_score(self, df: pd.DataFrame) -> float:
        """Calculate depth score based on response length and detail"""
        if df.empty:
            return 0.0

        avg_words = df["word_count"].mean()
        # Normalize to 0-1 scale (assuming 50 words is "good depth")
        depth = min(avg_words / 50.0, 1.0)
        return float(depth)

    def _calculate_constructiveness_score(self, responses: List[PersonaResponse]) -> float:
        """Calculate constructiveness (contains suggestions, ideas, not just complaints)"""
        if not responses:
            return 0.0

        constructive_keywords = ["suggest", "recommend", "could", "should", "would", "improve", "better", "idea", "propose"]
        constructive_count = sum(
            1 for r in responses
            if any(keyword in r.response.lower() for keyword in constructive_keywords)
        )

        return float(constructive_count / len(responses))

    def _calculate_specificity_score(self, df: pd.DataFrame) -> float:
        """Calculate specificity (mentions concrete details vs vague statements)"""
        if df.empty:
            return 0.0

        # Simple heuristic: longer responses with numbers/examples tend to be more specific
        specific_indicators = ["for example", "specifically", "in particular", "$", "%", "approximately"]

        specific_count = 0
        for text in df["response_text"]:
            if any(indicator in text.lower() for indicator in specific_indicators):
                specific_count += 1

        return float(specific_count / len(df))

    def _interpret_correlation(self, corr: float, p_value: float, var1: str, var2: str) -> str:
        """Generate human-readable interpretation of correlation"""
        if p_value >= 0.05:
            return f"No significant relationship between {var1} and {var2}"

        strength = "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"
        direction = "positive" if corr > 0 else "negative"

        return f"{strength.capitalize()} {direction} correlation: as {var1} increases, {var2} tends to {'increase' if corr > 0 else 'decrease'}"

    def _interpret_group_difference(self, means: Dict, p_value: float, group_var: str) -> str:
        """Generate interpretation for group differences"""
        if p_value >= 0.05:
            return f"No significant differences in sentiment across {group_var} groups"

        top_group = max(means.items(), key=lambda x: x[1])
        bottom_group = min(means.items(), key=lambda x: x[1])

        return f"Significant variation: {top_group[0]} shows highest sentiment ({top_group[1]:.2f}), while {bottom_group[0]} shows lowest ({bottom_group[1]:.2f})"

    def _label_segment(self, cluster_data: pd.DataFrame) -> str:
        """Generate descriptive label for behavioral segment"""
        avg_sentiment = cluster_data["sentiment"].mean()
        avg_length = cluster_data["response_length"].mean()

        if avg_sentiment > 0.2 and avg_length > 100:
            return "Enthusiastic Contributors"
        elif avg_sentiment > 0.2 and avg_length <= 100:
            return "Positive & Concise"
        elif avg_sentiment < -0.2 and avg_length > 100:
            return "Detailed Critics"
        elif avg_sentiment < -0.2 and avg_length <= 100:
            return "Skeptics"
        elif avg_length > 150:
            return "Verbose Respondents"
        else:
            return "Neutral Participants"

    def _find_optimal_clusters_elbow(self, data: np.ndarray, max_k: int = 5) -> int:
        """Find optimal number of clusters using elbow method"""
        if len(data) < 4:
            return 2

        inertias = []
        k_range = range(2, min(max_k + 1, len(data)))

        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(data)
            inertias.append(kmeans.inertia_)

        if len(inertias) < 2:
            return 2

        # Find elbow using second derivative
        deltas = np.diff(inertias)
        second_deltas = np.diff(deltas)

        if len(second_deltas) > 0:
            elbow_idx = int(np.argmax(second_deltas)) + 2
        else:
            elbow_idx = 2

        return max(2, min(elbow_idx, max_k))

    async def _get_focus_group(self, db: AsyncSession, focus_group_id: str) -> FocusGroup:
        """Fetch focus group from database"""
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()
        if not focus_group:
            raise ValueError("Focus group not found")
        return focus_group

    async def _get_responses(self, db: AsyncSession, focus_group_id: str) -> List[PersonaResponse]:
        """Fetch all responses for focus group"""
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        return result.scalars().all()

    async def _get_personas(self, db: AsyncSession, persona_ids: List[str]) -> Dict[str, Persona]:
        """Fetch personas by IDs"""
        result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = result.scalars().all()
        return {str(p.id): p for p in personas}

    def _empty_advanced_insights(self, focus_group_id: str) -> Dict[str, Any]:
        """Return empty structure when no data available"""
        return {
            "focus_group_id": focus_group_id,
            "demographic_correlations": {},
            "temporal_analysis": {},
            "behavioral_segments": {},
            "quality_metrics": {},
            "comparative_analysis": {},
            "outlier_detection": {},
            "engagement_patterns": {},
        }
