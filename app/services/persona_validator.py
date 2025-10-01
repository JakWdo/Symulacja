"""
Persona Validator - checks for diversity, uniqueness, and consistency
"""
import difflib
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PersonaValidator:
    """Validates persona quality and diversity"""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Args:
            similarity_threshold: Max similarity score (0-1) before flagging duplicates
        """
        self.similarity_threshold = similarity_threshold

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using difflib.

        Returns:
            Float between 0-1 (1 = identical, 0 = completely different)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize text
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # Use SequenceMatcher for similarity
        return difflib.SequenceMatcher(None, t1, t2).ratio()

    def check_background_uniqueness(
        self, personas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if background stories are sufficiently unique.

        Returns:
            Dict with uniqueness metrics and flagged duplicates
        """
        if len(personas) < 2:
            return {
                "is_unique": True,
                "avg_similarity": 0.0,
                "max_similarity": 0.0,
                "duplicate_pairs": [],
            }

        similarities = []
        duplicate_pairs = []

        for i in range(len(personas)):
            for j in range(i + 1, len(personas)):
                story1 = personas[i].get("background_story", "")
                story2 = personas[j].get("background_story", "")

                similarity = self.calculate_text_similarity(story1, story2)
                similarities.append(similarity)

                if similarity > self.similarity_threshold:
                    duplicate_pairs.append({
                        "index_1": i,
                        "index_2": j,
                        "similarity": similarity,
                        "story_1_snippet": story1[:100],
                        "story_2_snippet": story2[:100],
                    })

        return {
            "is_unique": len(duplicate_pairs) == 0,
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0.0,
            "max_similarity": max(similarities) if similarities else 0.0,
            "duplicate_pairs": duplicate_pairs,
            "total_comparisons": len(similarities),
        }

    def check_diversity_score(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall diversity score based on demographics and personality.

        Returns:
            Dict with diversity metrics
        """
        if len(personas) < 2:
            return {
                "diversity_score": 1.0,
                "demographic_diversity": 1.0,
                "personality_diversity": 1.0,
                "value_diversity": 1.0,
            }

        # Check demographic diversity
        ages = [p.get("age") for p in personas if p.get("age")]
        genders = [p.get("gender") for p in personas if p.get("gender")]
        locations = [p.get("location") for p in personas if p.get("location")]
        educations = [p.get("education_level") for p in personas if p.get("education_level")]
        incomes = [p.get("income_bracket") for p in personas if p.get("income_bracket")]

        def calc_unique_ratio(items: List[Any]) -> float:
            if not items:
                return 0.0
            return len(set(items)) / len(items)

        demographic_diversity = (
            calc_unique_ratio(ages) * 0.2 +
            calc_unique_ratio(genders) * 0.2 +
            calc_unique_ratio(locations) * 0.2 +
            calc_unique_ratio(educations) * 0.2 +
            calc_unique_ratio(incomes) * 0.2
        )

        # Check personality trait diversity (Big Five)
        trait_keys = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        trait_variances = []

        for key in trait_keys:
            values = [p.get(key) for p in personas if p.get(key) is not None]
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                trait_variances.append(variance)

        # Higher variance = more diversity
        personality_diversity = min(1.0, sum(trait_variances) / len(trait_variances)) if trait_variances else 0.5

        # Check value diversity
        all_values = []
        for p in personas:
            values = p.get("values", [])
            if values:
                all_values.extend(values)

        value_diversity = len(set(all_values)) / len(all_values) if all_values else 0.5

        # Overall diversity score
        diversity_score = (
            demographic_diversity * 0.4 +
            personality_diversity * 0.4 +
            value_diversity * 0.2
        )

        return {
            "diversity_score": diversity_score,
            "demographic_diversity": demographic_diversity,
            "personality_diversity": personality_diversity,
            "value_diversity": value_diversity,
        }

    def validate_personas(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run full validation suite on personas.

        Returns:
            Dict with all validation results
        """
        uniqueness_results = self.check_background_uniqueness(personas)
        diversity_results = self.check_diversity_score(personas)

        is_valid = (
            uniqueness_results["is_unique"] and
            diversity_results["diversity_score"] >= 0.5
        )

        results = {
            "is_valid": is_valid,
            "uniqueness": uniqueness_results,
            "diversity": diversity_results,
            "recommendations": [],
        }

        # Generate recommendations
        if not uniqueness_results["is_unique"]:
            results["recommendations"].append(
                f"Found {len(uniqueness_results['duplicate_pairs'])} similar persona pairs. "
                "Consider regenerating with higher temperature or more diverse prompts."
            )

        if diversity_results["diversity_score"] < 0.5:
            results["recommendations"].append(
                f"Low diversity score ({diversity_results['diversity_score']:.2f}). "
                "Ensure demographic distributions have sufficient variety."
            )

        if diversity_results["personality_diversity"] < 0.3:
            results["recommendations"].append(
                "Low personality diversity. Personas have similar Big Five trait profiles."
            )

        logger.info(
            "Persona validation completed",
            extra={
                "total_personas": len(personas),
                "is_valid": is_valid,
                "diversity_score": diversity_results["diversity_score"],
                "duplicates": len(uniqueness_results["duplicate_pairs"]),
            }
        )

        return results
