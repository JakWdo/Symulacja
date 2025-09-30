from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from scipy.spatial.distance import cosine
from scipy import stats
import json

from app.models import PersonaResponse, FocusGroup
from app.core.config import get_settings

settings = get_settings()


class PolarizationService:
    """
    Detect and analyze polarization in focus group responses
    Identifies opinion clusters and measures sentiment divergence
    """

    def __init__(self):
        self.settings = settings
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )

    async def analyze_polarization(
        self, db: AsyncSession, focus_group_id: str
    ) -> Dict[str, Any]:
        """
        Comprehensive polarization analysis for a focus group
        Returns polarization score, clusters, and sentiment analysis
        """

        # Load all responses
        result = await db.execute(
            select(PersonaResponse).where(
                PersonaResponse.focus_group_id == focus_group_id
            )
        )
        responses = result.scalars().all()

        if len(responses) < 3:
            return {
                "polarization_score": 0.0,
                "clusters": [],
                "error": "Insufficient responses for polarization analysis",
            }

        # Group responses by question
        responses_by_question = {}
        for response in responses:
            if response.question not in responses_by_question:
                responses_by_question[response.question] = []
            responses_by_question[response.question].append(response)

        # Analyze each question
        question_analyses = []
        overall_polarization_scores = []

        for question, question_responses in responses_by_question.items():
            analysis = await self._analyze_question_polarization(question, question_responses)
            question_analyses.append(analysis)
            overall_polarization_scores.append(analysis["polarization_score"])

        # Calculate overall polarization
        overall_polarization = np.mean(overall_polarization_scores)

        # Update focus group
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one()
        focus_group.polarization_score = overall_polarization
        focus_group.polarization_clusters = {
            "questions": question_analyses,
            "overall": {
                "polarization_score": overall_polarization,
                "num_questions": len(question_analyses),
            },
        }

        await db.commit()

        return {
            "focus_group_id": str(focus_group_id),
            "overall_polarization_score": overall_polarization,
            "polarization_level": self._categorize_polarization(overall_polarization),
            "questions": question_analyses,
        }

    async def _analyze_question_polarization(
        self, question: str, responses: List[PersonaResponse]
    ) -> Dict[str, Any]:
        """Analyze polarization for a single question"""

        if len(responses) < 2:
            return {
                "question": question,
                "polarization_score": 0.0,
                "clusters": [],
                "num_responses": len(responses),
            }

        # Generate embeddings for all responses
        response_texts = [r.response for r in responses]
        embeddings_list = await self.embedding_model.aembed_documents(response_texts)
        embeddings = np.array(embeddings_list)

        # Perform clustering
        clusters, cluster_labels = self._cluster_responses(embeddings, min_cluster_size=2)

        # Calculate polarization metrics
        polarization_score = self._calculate_polarization_score(
            embeddings, cluster_labels
        )

        # Sentiment analysis
        sentiment_analysis = self._analyze_sentiment_divergence(
            response_texts, cluster_labels
        )

        # Build cluster details
        cluster_details = []
        for cluster_id in range(len(clusters)):
            cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
            cluster_responses = [responses[i] for i in cluster_indices]

            cluster_details.append(
                {
                    "cluster_id": cluster_id,
                    "size": len(cluster_responses),
                    "persona_ids": [str(r.persona_id) for r in cluster_responses],
                    "representative_response": self._get_representative_response(
                        cluster_responses, embeddings[cluster_indices]
                    ),
                    "avg_sentiment": float(
                        np.mean([sentiment_analysis["sentiments"][i] for i in cluster_indices])
                    ),
                }
            )

        return {
            "question": question,
            "polarization_score": polarization_score,
            "num_clusters": len(clusters),
            "clusters": cluster_details,
            "sentiment_divergence": sentiment_analysis["divergence"],
            "num_responses": len(responses),
        }

    def _cluster_responses(
        self, embeddings: np.ndarray, min_cluster_size: int = 2
    ) -> Tuple[List[np.ndarray], List[int]]:
        """
        Cluster responses using K-means or DBSCAN
        Returns cluster centroids and labels
        """

        n_samples = len(embeddings)

        # Try K-means with different numbers of clusters
        if n_samples >= 4:
            # Use elbow method to find optimal k
            optimal_k = self._find_optimal_clusters(embeddings, max_k=min(5, n_samples // 2))
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            clusters = [kmeans.cluster_centers_[i] for i in range(optimal_k)]

        elif n_samples >= 2:
            # Simple binary clustering
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            clusters = [kmeans.cluster_centers_[i] for i in range(2)]

        else:
            # Single cluster
            labels = [0] * n_samples
            clusters = [np.mean(embeddings, axis=0)]

        return clusters, labels.tolist()

    def _find_optimal_clusters(self, embeddings: np.ndarray, max_k: int = 5) -> int:
        """Find optimal number of clusters using elbow method"""
        inertias = []
        k_range = range(2, min(max_k + 1, len(embeddings)))

        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            inertias.append(kmeans.inertia_)

        if len(inertias) < 2:
            return 2

        # Find elbow using second derivative
        deltas = np.diff(inertias)
        second_deltas = np.diff(deltas)

        if len(second_deltas) > 0:
            elbow_idx = np.argmax(second_deltas) + 2
        else:
            elbow_idx = 2

        return min(elbow_idx, max_k)

    def _calculate_polarization_score(
        self, embeddings: np.ndarray, labels: List[int]
    ) -> float:
        """
        Calculate polarization score (0-1 scale)
        Higher score = more polarization
        """

        unique_labels = set(labels)
        n_clusters = len(unique_labels)

        if n_clusters <= 1:
            return 0.0

        # Calculate inter-cluster distance (higher = more polarized)
        cluster_centroids = []
        for label in unique_labels:
            cluster_embeddings = embeddings[np.array(labels) == label]
            centroid = np.mean(cluster_embeddings, axis=0)
            cluster_centroids.append(centroid)

        # Average distance between cluster centroids
        inter_cluster_distances = []
        for i in range(len(cluster_centroids)):
            for j in range(i + 1, len(cluster_centroids)):
                dist = cosine(cluster_centroids[i], cluster_centroids[j])
                inter_cluster_distances.append(dist)

        avg_inter_cluster_dist = np.mean(inter_cluster_distances) if inter_cluster_distances else 0

        # Calculate intra-cluster cohesion (lower = more cohesive)
        intra_cluster_distances = []
        for label in unique_labels:
            cluster_embeddings = embeddings[np.array(labels) == label]
            if len(cluster_embeddings) > 1:
                centroid = np.mean(cluster_embeddings, axis=0)
                for emb in cluster_embeddings:
                    dist = cosine(emb, centroid)
                    intra_cluster_distances.append(dist)

        avg_intra_cluster_dist = np.mean(intra_cluster_distances) if intra_cluster_distances else 0

        # Polarization = inter-cluster distance / (inter + intra)
        # Normalized to 0-1 scale
        if avg_inter_cluster_dist + avg_intra_cluster_dist > 0:
            polarization = avg_inter_cluster_dist / (avg_inter_cluster_dist + avg_intra_cluster_dist)
        else:
            polarization = 0.0

        # Scale by number of clusters (more clusters = less polarization)
        cluster_penalty = 1 / (1 + np.log(n_clusters))
        polarization = polarization * cluster_penalty

        return float(np.clip(polarization, 0, 1))

    def _analyze_sentiment_divergence(
        self, responses: List[str], labels: List[int]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment divergence across clusters
        Simple sentiment scoring based on positive/negative words
        """

        positive_words = {
            "good", "great", "excellent", "love", "like", "enjoy", "positive",
            "amazing", "wonderful", "fantastic", "best", "happy", "yes", "agree"
        }
        negative_words = {
            "bad", "terrible", "hate", "dislike", "awful", "worst", "negative",
            "horrible", "poor", "no", "disagree", "concern", "worried", "against"
        }

        sentiments = []
        for response in responses:
            response_lower = response.lower()
            pos_count = sum(1 for word in positive_words if word in response_lower)
            neg_count = sum(1 for word in negative_words if word in response_lower)

            # Sentiment score: -1 to 1
            total = pos_count + neg_count
            if total > 0:
                sentiment = (pos_count - neg_count) / total
            else:
                sentiment = 0.0

            sentiments.append(sentiment)

        # Calculate divergence across clusters
        unique_labels = set(labels)
        cluster_sentiments = {}
        for label in unique_labels:
            cluster_sentiments[label] = [
                sentiments[i] for i, l in enumerate(labels) if l == label
            ]

        # Variance in sentiment across clusters
        cluster_means = [np.mean(cluster_sentiments[label]) for label in unique_labels]
        divergence = float(np.var(cluster_means)) if len(cluster_means) > 1 else 0.0

        return {
            "sentiments": sentiments,
            "divergence": divergence,
            "cluster_means": {int(k): float(np.mean(v)) for k, v in cluster_sentiments.items()},
        }

    def _get_representative_response(
        self, responses: List[PersonaResponse], embeddings: np.ndarray
    ) -> str:
        """Get the most representative response from a cluster"""
        if len(responses) == 1:
            return responses[0].response

        # Find response closest to centroid
        centroid = np.mean(embeddings, axis=0)
        distances = [cosine(emb, centroid) for emb in embeddings]
        min_idx = np.argmin(distances)

        return responses[min_idx].response

    def _categorize_polarization(self, score: float) -> str:
        """Categorize polarization level"""
        if score < 0.2:
            return "Very Low - High Consensus"
        elif score < 0.4:
            return "Low - General Agreement"
        elif score < 0.6:
            return "Moderate - Mixed Opinions"
        elif score < 0.8:
            return "High - Significant Divide"
        else:
            return "Very High - Strong Polarization"