"""Focus group insight scoring and thematic analysis."""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Tuple

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from scipy.spatial.distance import cosine
from sklearn.cluster import KMeans
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import FocusGroup, PersonaResponse
from app.services.insight_rater_service import InsightRaterService

settings = get_settings()
logger = logging.getLogger(__name__)


class InsightService:
    """Generate qualitative and quantitative insights for a focus group."""

    _POSITIVE_WORDS = {
        "good",
        "great",
        "excellent",
        "love",
        "like",
        "enjoy",
        "positive",
        "amazing",
        "wonderful",
        "fantastic",
        "best",
        "happy",
        "yes",
        "agree",
        "excited",
        "helpful",
        "valuable",
        "useful",
    }
    _NEGATIVE_WORDS = {
        "bad",
        "terrible",
        "hate",
        "dislike",
        "awful",
        "worst",
        "negative",
        "horrible",
        "poor",
        "no",
        "disagree",
        "concern",
        "worried",
        "against",
        "confusing",
        "hard",
        "difficult",
    }
    _STOP_WORDS = {
        "the",
        "and",
        "that",
        "with",
        "this",
        "from",
        "have",
        "your",
        "about",
        "would",
        "which",
        "into",
        "there",
        "their",
        "while",
        "them",
        "they",
        "what",
        "when",
        "where",
        "really",
        "should",
        "because",
        "could",
        "maybe",
        "also",
        "such",
        "much",
        "very",
        "make",
        "made",
        "just",
        "like",
        "can",
        "will",
        "need",
        "have",
    }

    def __init__(self) -> None:
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GOOGLE_API_KEY,
        )

    async def generate_focus_group_insights(
        self, db: AsyncSession, focus_group_id: str
    ) -> Dict[str, Any]:
        """Compute insight scores, sentiment, and thematic summaries."""

        focus_group = await self._get_focus_group(db, focus_group_id)

        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
            .order_by(PersonaResponse.created_at)
        )
        responses = result.scalars().all()

        if not responses:
            empty_payload = self._empty_insight_payload(focus_group_id)
            focus_group.polarization_score = 0.0
            focus_group.polarization_clusters = empty_payload
            await db.commit()
            return empty_payload

        # Group responses by question prompt
        responses_by_question: Dict[str, List[PersonaResponse]] = {}
        for response in responses:
            responses_by_question.setdefault(response.question, []).append(response)

        question_insights: List[Dict[str, Any]] = []
        persona_stats: Dict[str, Dict[str, Any]] = {}
        theme_counter: Counter[str] = Counter()
        avg_sentiments: List[float] = []
        consensus_scores: List[float] = []
        idea_scores: List[float] = []
        evidence_samples: List[Dict[str, Any]] = []

        for question, question_responses in responses_by_question.items():
            texts = [resp.response for resp in question_responses]
            sentiments = [self._sentiment_score(text) for text in texts]
            avg_sentiment = float(np.mean(sentiments)) if sentiments else 0.0

            embeddings = None
            cluster_labels: List[int]
            consensus = 1.0

            if len(texts) >= 2 and settings.GOOGLE_API_KEY:
                try:
                    embeddings = np.array(
                        await self.embedding_model.aembed_documents(texts)
                    )
                except Exception:
                    embeddings = None

            if embeddings is not None and len(texts) == len(embeddings):
                _, cluster_labels = self._cluster_responses(embeddings)
                polarization = self._calculate_polarization_score(embeddings, cluster_labels)
                consensus = float(np.clip(1 - polarization, 0, 1))
            else:
                cluster_labels = [0] * len(texts)
                consensus = 1.0 if len(texts) <= 1 else 0.6

            idea_score = self._compute_idea_score(avg_sentiment, consensus)

            top_quote_indices = self._select_top_quotes(sentiments, limit=5)
            top_quotes = [
                {
                    "persona_id": str(question_responses[idx].persona_id),
                    "response": question_responses[idx].response,
                    "sentiment": sentiments[idx],
                    "consistency_score": question_responses[idx].consistency_score,
                    "created_at": question_responses[idx].created_at.isoformat(),
                }
                for idx in top_quote_indices
            ]

            participants = sorted({str(resp.persona_id) for resp in question_responses})

            question_insights.append(
                {
                    "question": question,
                    "idea_score": idea_score,
                    "consensus": consensus,
                    "avg_sentiment": avg_sentiment,
                    "response_count": len(question_responses),
                    "top_quotes": top_quotes,
                    "participants": participants,
                }
            )

            for idx, resp in enumerate(question_responses):
                persona_id = str(resp.persona_id)
                stats = persona_stats.setdefault(
                    persona_id,
                    {
                        "persona_id": persona_id,
                        "contribution_count": 0,
                        "sentiment_total": 0.0,
                        "last_activity": None,
                        "average_response_time_ms": 0.0,
                    },
                )
                stats["contribution_count"] += 1
                stats["sentiment_total"] += sentiments[idx]
                response_time = resp.response_time_ms or 0.0
                stats["average_response_time_ms"] += response_time
                timestamp = resp.created_at.isoformat()
                if stats["last_activity"] is None or stats["last_activity"] < timestamp:
                    stats["last_activity"] = timestamp

                evidence_samples.append(
                    {
                        "persona_id": persona_id,
                        "question": question,
                        "response": resp.response,
                        "sentiment": sentiments[idx],
                        "consistency_score": resp.consistency_score,
                        "created_at": resp.created_at.isoformat(),
                    }
                )

            for resp in question_responses:
                theme_counter.update(self._extract_keywords(resp.response))

            avg_sentiments.append(avg_sentiment)
            consensus_scores.append(consensus)
            idea_scores.append(idea_score)

        personas_engagement = self._normalize_persona_engagement(persona_stats)

        fallback_idea_score = float(np.mean(idea_scores)) if idea_scores else 0.0
        overall_consensus = float(np.mean(consensus_scores)) if consensus_scores else 0.0
        overall_sentiment = float(np.mean(avg_sentiments)) if avg_sentiments else 0.0

        sentiment_values = [self._sentiment_score(resp.response) for resp in responses]
        positive_ratio = (
            sum(1 for val in sentiment_values if val > 0.15) / len(sentiment_values)
            if sentiment_values
            else 0.0
        )
        negative_ratio = (
            sum(1 for val in sentiment_values if val < -0.15) / len(sentiment_values)
            if sentiment_values
            else 0.0
        )

        engagement_metrics = self._compute_engagement_metrics(focus_group, responses)

        key_themes = self._build_theme_list(theme_counter, responses, limit=6)

        rating_payload = {
            "focus_group_id": focus_group_id,
            "total_responses": len(responses),
            "participant_count": len({str(resp.persona_id) for resp in responses}),
            "metrics": {
                "consensus": overall_consensus,
                "average_sentiment": overall_sentiment,
                "sentiment_summary": {
                    "positive_ratio": positive_ratio,
                    "negative_ratio": negative_ratio,
                    "neutral_ratio": max(0.0, 1.0 - positive_ratio - negative_ratio),
                },
                "engagement": engagement_metrics,
            },
            "key_themes": key_themes,
            "question_breakdown": question_insights,
        }

        llm_ratings: Dict[str, Any] = {}
        if settings.GOOGLE_API_KEY:
            try:
                rater = InsightRaterService(use_pro_model=True)
                llm_ratings = await rater.rate_focus_group(rating_payload)
            except Exception as exc:  # pragma: no cover - falls back to heuristic
                logger.warning(
                    "InsightRaterService failed, falling back to heuristic score",
                    exc_info=exc,
                    extra={"focus_group_id": focus_group_id},
                )

        overall_idea_score = float(
            np.clip(llm_ratings.get("idea_score", fallback_idea_score), 0.0, 100.0)
        )
        llm_confidence = float(np.clip(llm_ratings.get("confidence", 0.0), 0.0, 1.0))
        llm_rationale = llm_ratings.get("rationale", "")

        analysis_payload = {
            "focus_group_id": focus_group_id,
            "idea_score": overall_idea_score,
            "idea_grade": self._grade_score(overall_idea_score),
            "metrics": {
                "consensus": overall_consensus,
                "average_sentiment": overall_sentiment,
                "sentiment_summary": {
                    "positive_ratio": positive_ratio,
                    "negative_ratio": negative_ratio,
                    "neutral_ratio": max(0.0, 1.0 - positive_ratio - negative_ratio),
                },
                "engagement": engagement_metrics,
            },
            "signal_breakdown": self._compose_signal_breakdown(
                llm_ratings,
                overall_consensus,
                overall_sentiment,
                positive_ratio,
                negative_ratio,
                engagement_metrics,
            ),
            "persona_patterns": self._build_persona_patterns(
                personas_engagement,
                overall_sentiment,
            ),
            "evidence_feed": self._build_evidence_feed(evidence_samples),
            "llm_confidence": llm_confidence,
            "llm_rationale": llm_rationale,
        }

        # Persist summary for quick retrieval in the focus group record
        focus_group.polarization_score = float(
            np.clip(overall_idea_score / 100.0, 0.0, 1.0)
        )
        focus_group.polarization_clusters = analysis_payload

        avg_consistency = engagement_metrics.get("consistency_score")
        if avg_consistency is not None:
            focus_group.overall_consistency_score = avg_consistency

        await db.commit()
        return analysis_payload

    async def _get_focus_group(
        self, db: AsyncSession, focus_group_id: str
    ) -> FocusGroup:
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()
        if not focus_group:
            raise ValueError("Focus group not found")
        return focus_group

    def _empty_insight_payload(self, focus_group_id: str) -> Dict[str, Any]:
        return {
            "focus_group_id": focus_group_id,
            "idea_score": 0.0,
            "idea_grade": "Insufficient data",
            "metrics": {
                "consensus": 0.0,
                "average_sentiment": 0.0,
                "sentiment_summary": {
                    "positive_ratio": 0.0,
                    "negative_ratio": 0.0,
                    "neutral_ratio": 1.0,
                },
                "engagement": {
                    "average_response_time_ms": None,
                    "completion_rate": 0.0,
                    "consistency_score": None,
                },
            },
            "signal_breakdown": {
                "strengths": [],
                "risks": [],
                "opportunities": [],
            },
            "persona_patterns": [],
            "evidence_feed": {
                "positives": [],
                "negatives": [],
            },
            "llm_confidence": 0.0,
            "llm_rationale": "",
        }

    def _normalize_persona_engagement(
        self, persona_stats: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        personas_engagement: List[Dict[str, Any]] = []
        for persona_id, stats in persona_stats.items():
            contributions = stats["contribution_count"]
            avg_sentiment = (
                stats["sentiment_total"] / contributions if contributions else 0.0
            )
            avg_response_time = (
                stats["average_response_time_ms"] / contributions if contributions else 0.0
            )

            personas_engagement.append(
                {
                    "persona_id": persona_id,
                    "contribution_count": contributions,
                    "avg_sentiment": avg_sentiment,
                    "average_response_time_ms": avg_response_time,
                    "last_activity": stats["last_activity"],
                }
            )

        personas_engagement.sort(
            key=lambda item: (item["contribution_count"], item["avg_sentiment"]),
            reverse=True,
        )
        return personas_engagement

    def _compose_signal_breakdown(
        self,
        llm_ratings: Dict[str, Any],
        consensus: float,
        sentiment: float,
        positive_ratio: float,
        negative_ratio: float,
        engagement_metrics: Dict[str, Any],
    ) -> Dict[str, List[Dict[str, Any]]]:
        strengths = llm_ratings.get("strengths") or []
        risks = llm_ratings.get("risks") or []
        opportunities = llm_ratings.get("opportunities") or []

        if not strengths:
            strengths = []
            if consensus >= 0.7:
                strengths.append(
                    {
                        "title": "Silny konsensus",
                        "summary": "Większość uczestników zgadza się co do wartości propozycji, co zmniejsza ryzyko polarizacji.",
                    }
                )
            if sentiment >= 0.2:
                strengths.append(
                    {
                        "title": "Pozytywny odbiór",
                        "summary": "Średni sentyment jest powyżej progu 0.2, co sugeruje autentyczne poparcie dla konceptu.",
                    }
                )
            if positive_ratio > 0.5:
                strengths.append(
                    {
                        "title": "Przewaga pozytywnych odpowiedzi",
                        "summary": "Ponad połowa wypowiedzi ma pozytywny ton, co wzmacnia narrację sukcesu.",
                    }
                )

        if not risks:
            risks = []
            if consensus < 0.55:
                risks.append(
                    {
                        "title": "Rozbieżne opinie",
                        "summary": "Koncentracja opinii jest niska – koncepcja może wymagać doprecyzowania dla poszczególnych segmentów.",
                    }
                )
            if negative_ratio > 0.25:
                risks.append(
                    {
                        "title": "Istotny odsetek krytyki",
                        "summary": "Ponad jedna czwarta wypowiedzi ma negatywny charakter, co wskazuje na konkretne bariery adopcji.",
                    }
                )
            completion_rate = engagement_metrics.get("completion_rate") or 0.0
            if completion_rate < 0.6:
                risks.append(
                    {
                        "title": "Niski completion rate",
                        "summary": "Uczestnicy nie kończą scenariusza – format badań może wymagać skrócenia lub doprecyzowania.",
                    }
                )

        if not opportunities:
            opportunities = []
            if sentiment >= -0.05 and negative_ratio > 0.15:
                opportunities.append(
                    {
                        "title": "Potencjał do adresowania obaw",
                        "summary": "Krytyczne komentarze są konstruktywne – można je przekuć w roadmapę poprawek.",
                    }
                )
            consistency = engagement_metrics.get("consistency_score")
            if consistency is not None and consistency >= 0.7:
                opportunities.append(
                    {
                        "title": "Spójne zachowania person",
                        "summary": "Stabilne odpowiedzi sugerują, że można szybko iterować komunikację bez ryzyka utraty wiarygodności.",
                    }
                )

        return {
            "strengths": strengths,
            "risks": risks,
            "opportunities": opportunities,
        }

    def _build_persona_patterns(
        self,
        personas_engagement: List[Dict[str, Any]],
        overall_sentiment: float,
    ) -> List[Dict[str, Any]]:
        if not personas_engagement:
            return []

        contribution_values = [p["contribution_count"] for p in personas_engagement]
        avg_contribution = float(np.mean(contribution_values)) if contribution_values else 0.0

        patterns: List[Dict[str, Any]] = []
        for persona in personas_engagement:
            sentiment_delta = persona["avg_sentiment"] - overall_sentiment
            contributions = persona["contribution_count"]
            classification = "neutral"

            if sentiment_delta >= 0.15:
                classification = "champion"
            elif sentiment_delta <= -0.15:
                classification = "detractor"
            elif contributions < max(1.0, avg_contribution * 0.6):
                classification = "low_engagement"

            summary_bits: List[str] = []
            summary_bits.append(
                f"Sentiment delta vs średnia: {sentiment_delta:+.2f}"
            )
            summary_bits.append(f"Wkład: {contributions} odpowiedzi")
            if persona["average_response_time_ms"]:
                summary_bits.append(
                    f"Śr. czas reakcji: {persona['average_response_time_ms']:.0f} ms"
                )

            patterns.append(
                {
                    "persona_id": persona["persona_id"],
                    "classification": classification,
                    "avg_sentiment": persona["avg_sentiment"],
                    "contribution_count": contributions,
                    "last_activity": persona["last_activity"],
                    "summary": "; ".join(summary_bits),
                }
            )

        return patterns

    def _build_evidence_feed(
        self, evidence_samples: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not evidence_samples:
            return {"positives": [], "negatives": []}

        positives = [
            sample
            for sample in evidence_samples
            if sample["sentiment"] >= 0.15
        ]
        negatives = [
            sample
            for sample in evidence_samples
            if sample["sentiment"] <= -0.15
        ]

        positives.sort(key=lambda item: item["sentiment"], reverse=True)
        negatives.sort(key=lambda item: item["sentiment"])

        def _format(sample: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "persona_id": sample["persona_id"],
                "question": sample["question"],
                "response": sample["response"],
                "sentiment": sample["sentiment"],
                "consistency_score": sample.get("consistency_score"),
                "created_at": sample.get("created_at"),
            }

        return {
            "positives": [_format(item) for item in positives[:6]],
            "negatives": [_format(item) for item in negatives[:6]],
        }

    def _compute_engagement_metrics(
        self, focus_group: FocusGroup, responses: List[PersonaResponse]
    ) -> Dict[str, Any]:
        avg_response_time = (
            float(
                np.mean(
                    [resp.response_time_ms for resp in responses if resp.response_time_ms]
                )
            )
            if responses
            else None
        )
        expected_total = 0
        if focus_group.persona_ids and focus_group.questions:
            expected_total = len(focus_group.persona_ids) * len(focus_group.questions)
        completion_rate = (
            len(responses) / expected_total if expected_total else 0.0
        )
        consistency_scores = [
            resp.consistency_score
            for resp in responses
            if resp.consistency_score is not None
        ]
        avg_consistency = (
            float(np.mean(consistency_scores)) if consistency_scores else None
        )

        return {
            "average_response_time_ms": avg_response_time,
            "completion_rate": float(np.clip(completion_rate, 0, 1)),
            "consistency_score": avg_consistency,
        }

    def _sentiment_score(self, text: str) -> float:
        lowered = text.lower()
        pos = sum(1 for token in self._POSITIVE_WORDS if token in lowered)
        neg = sum(1 for token in self._NEGATIVE_WORDS if token in lowered)
        total = pos + neg
        if total == 0:
            return 0.0
        return float((pos - neg) / total)

    def sentiment_score(self, text: str) -> float:
        """Public wrapper for sentiment scoring."""
        return self._sentiment_score(text)

    def _extract_keywords(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z]{3,}", text.lower())
        return [
            token
            for token in tokens
            if token not in self._STOP_WORDS and len(token) > 3
        ]

    def _select_top_quotes(self, sentiments: List[float], limit: int = 5) -> List[int]:
        if not sentiments:
            return []
        ranked = sorted(
            range(len(sentiments)),
            key=lambda idx: (abs(sentiments[idx]), sentiments[idx]),
            reverse=True,
        )
        return ranked[:limit]

    def _compute_idea_score(self, avg_sentiment: float, consensus: float) -> float:
        sentiment_norm = (avg_sentiment + 1.0) / 2.0
        score = sentiment_norm * 0.6 + consensus * 0.4
        return float(np.clip(score * 100.0, 0.0, 100.0))

    def _grade_score(self, score: float) -> str:
        if score >= 85:
            return "Excellent potential"
        if score >= 70:
            return "Strong potential"
        if score >= 55:
            return "Moderate potential"
        if score >= 40:
            return "Needs validation"
        return "High risk"

    def _build_theme_list(
        self,
        counter: Counter[str],
        responses: List[PersonaResponse],
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        themes: List[Dict[str, Any]] = []
        for keyword, mentions in counter.most_common(limit):
            quote = next(
                (
                    resp.response
                    for resp in responses
                    if keyword in resp.response.lower()
                ),
                None,
            )
            themes.append(
                {
                    "keyword": keyword,
                    "mentions": mentions,
                    "representative_quote": quote,
                }
            )
        return themes

    def _cluster_responses(
        self, embeddings: np.ndarray
    ) -> Tuple[List[np.ndarray], List[int]]:
        n_samples = len(embeddings)
        if n_samples < 2:
            return [np.mean(embeddings, axis=0)], [0]

        if n_samples >= 4:
            optimal_k = self._find_optimal_clusters(embeddings, max_k=min(5, n_samples // 2))
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            clusters = [kmeans.cluster_centers_[i] for i in range(optimal_k)]
        else:
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            clusters = [kmeans.cluster_centers_[i] for i in range(2)]

        return clusters, labels.tolist()

    def _find_optimal_clusters(self, embeddings: np.ndarray, max_k: int = 5) -> int:
        inertias = []
        k_range = range(2, min(max_k + 1, len(embeddings)))
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)

        if len(inertias) < 2:
            return 2

        deltas = np.diff(inertias)
        second_deltas = np.diff(deltas)
        if len(second_deltas) > 0:
            elbow_idx = int(np.argmax(second_deltas)) + 2
        else:
            elbow_idx = 2
        return max(2, min(elbow_idx, max_k))

    def _calculate_polarization_score(
        self, embeddings: np.ndarray, labels: List[int]
    ) -> float:
        unique_labels = set(labels)
        if len(unique_labels) <= 1:
            return 0.0

        cluster_centroids = []
        for label in unique_labels:
            cluster_embeddings = embeddings[np.array(labels) == label]
            centroid = np.mean(cluster_embeddings, axis=0)
            cluster_centroids.append(centroid)

        inter_cluster_distances = []
        for i in range(len(cluster_centroids)):
            for j in range(i + 1, len(cluster_centroids)):
                dist = cosine(cluster_centroids[i], cluster_centroids[j])
                if not math.isnan(dist):
                    inter_cluster_distances.append(dist)

        avg_inter = np.mean(inter_cluster_distances) if inter_cluster_distances else 0.0

        intra_cluster_distances = []
        for label in unique_labels:
            cluster_embeddings = embeddings[np.array(labels) == label]
            if len(cluster_embeddings) > 1:
                centroid = np.mean(cluster_embeddings, axis=0)
                for emb in cluster_embeddings:
                    dist = cosine(emb, centroid)
                    if not math.isnan(dist):
                        intra_cluster_distances.append(dist)

        avg_intra = np.mean(intra_cluster_distances) if intra_cluster_distances else 0.0
        if avg_inter + avg_intra == 0:
            return 0.0

        polarization = avg_inter / (avg_inter + avg_intra)
        cluster_penalty = 1 / (1 + np.log(len(unique_labels)))
        return float(np.clip(polarization * cluster_penalty, 0.0, 1.0))
