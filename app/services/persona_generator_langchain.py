"""
LangChain-based Persona Generator using Gemini models
Replaces the original OpenAI/Anthropic implementation with LangChain abstractions
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from scipy import stats
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import get_settings
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    DEFAULT_EDUCATION_LEVELS,
    DEFAULT_INCOME_BRACKETS,
    DEFAULT_LOCATIONS,
)
from app.models import Persona

settings = get_settings()


@dataclass
class DemographicDistribution:
    """Target population distribution"""
    age_groups: Dict[str, float]
    genders: Dict[str, float]
    education_levels: Dict[str, float]
    income_brackets: Dict[str, float]
    locations: Dict[str, float]


class PersonaGeneratorLangChain:
    """Generate statistically representative personas using LangChain + Gemini"""

    def __init__(self):
        self.settings = settings
        self._rng = np.random.default_rng(self.settings.RANDOM_SEED)

        # Initialize LangChain Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.DEFAULT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )

        # Setup output parser for structured JSON responses
        self.json_parser = JsonOutputParser()

        # Create prompt template for persona generation
        self.persona_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a market research expert creating realistic synthetic personas. Always respond with valid JSON."),
            ("user", "{prompt}")
        ])

        # Create LangChain chain for persona generation
        self.persona_chain = (
            self.persona_prompt
            | self.llm
            | self.json_parser
        )

    def sample_demographic_profile(
        self, distribution: DemographicDistribution, n_samples: int = 1
    ) -> List[Dict[str, Any]]:
        """Sample demographic profiles based on target distribution"""
        profiles = []

        for _ in range(n_samples):
            age_groups = self._prepare_distribution(
                distribution.age_groups, DEFAULT_AGE_GROUPS
            )
            genders = self._prepare_distribution(distribution.genders, DEFAULT_GENDERS)
            education_levels = self._prepare_distribution(
                distribution.education_levels, DEFAULT_EDUCATION_LEVELS
            )
            income_brackets = self._prepare_distribution(
                distribution.income_brackets, DEFAULT_INCOME_BRACKETS
            )
            locations = self._prepare_distribution(
                distribution.locations, DEFAULT_LOCATIONS
            )
            profile = {
                "age_group": self._weighted_sample(age_groups),
                "gender": self._weighted_sample(genders),
                "education_level": self._weighted_sample(education_levels),
                "income_bracket": self._weighted_sample(income_brackets),
                "location": self._weighted_sample(locations),
            }
            profiles.append(profile)

        return profiles

    def _weighted_sample(self, distribution: Dict[str, float]) -> str:
        """Sample from weighted distribution"""
        if not distribution:
            raise ValueError("Distribution cannot be empty")
        categories = list(distribution.keys())
        weights = list(distribution.values())
        return self._rng.choice(categories, p=weights)

    def _prepare_distribution(
        self, distribution: Dict[str, float], fallback: Dict[str, float]
    ) -> Dict[str, float]:
        if not distribution:
            return fallback
        total = sum(distribution.values())
        if total <= 0:
            return fallback
        normalized = {key: value / total for key, value in distribution.items()}
        normalized_total = sum(normalized.values())
        if not np.isclose(normalized_total, 1.0):
            normalized = {
                key: value / normalized_total for key, value in normalized.items()
            }
        return normalized

    def sample_big_five_traits(self) -> Dict[str, float]:
        """Sample Big Five personality traits from normal distributions"""
        return {
            "openness": np.clip(self._rng.normal(0.5, 0.15), 0, 1),
            "conscientiousness": np.clip(self._rng.normal(0.5, 0.15), 0, 1),
            "extraversion": np.clip(self._rng.normal(0.5, 0.15), 0, 1),
            "agreeableness": np.clip(self._rng.normal(0.5, 0.15), 0, 1),
            "neuroticism": np.clip(self._rng.normal(0.5, 0.15), 0, 1),
        }

    def sample_cultural_dimensions(self) -> Dict[str, float]:
        """Sample Hofstede cultural dimensions"""
        return {
            "power_distance": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "individualism": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "masculinity": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "uncertainty_avoidance": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "long_term_orientation": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
            "indulgence": np.clip(self._rng.normal(0.5, 0.2), 0, 1),
        }

    async def generate_persona_personality(
        self, demographic_profile: Dict[str, Any], psychological_profile: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate persona personality using LangChain + Gemini"""

        prompt_text = self._create_persona_prompt(demographic_profile, psychological_profile)

        # Use LangChain chain to generate structured response
        try:
            response = await self.persona_chain.ainvoke({"prompt": prompt_text})
            return prompt_text, response
        except Exception as e:
            # Fallback for parsing errors
            raise ValueError(f"Failed to generate persona: {str(e)}")

    def _create_persona_prompt(
        self, demographic: Dict[str, Any], psychological: Dict[str, Any]
    ) -> str:
        """Create prompt for LLM persona generation"""
        return f"""You are creating a synthetic persona for market research. Generate a detailed, realistic personality profile based on the following attributes:

DEMOGRAPHICS:
- Age Group: {demographic.get('age_group')}
- Gender: {demographic.get('gender')}
- Education: {demographic.get('education_level')}
- Income: {demographic.get('income_bracket')}
- Location: {demographic.get('location')}

PSYCHOLOGICAL PROFILE (Big Five, 0-1 scale):
- Openness: {psychological.get('openness', 0.5):.2f}
- Conscientiousness: {psychological.get('conscientiousness', 0.5):.2f}
- Extraversion: {psychological.get('extraversion', 0.5):.2f}
- Agreeableness: {psychological.get('agreeableness', 0.5):.2f}
- Neuroticism: {psychological.get('neuroticism', 0.5):.2f}

CULTURAL DIMENSIONS (Hofstede, 0-1 scale):
- Power Distance: {psychological.get('power_distance', 0.5):.2f}
- Individualism: {psychological.get('individualism', 0.5):.2f}
- Masculinity: {psychological.get('masculinity', 0.5):.2f}
- Uncertainty Avoidance: {psychological.get('uncertainty_avoidance', 0.5):.2f}
- Long-term Orientation: {psychological.get('long_term_orientation', 0.5):.2f}
- Indulgence: {psychological.get('indulgence', 0.5):.2f}

Generate a JSON response with:
1. "background_story": A brief 2-3 sentence background (career, life situation, family)
2. "values": List of 5-7 core values that guide their decisions
3. "interests": List of 5-7 interests/hobbies
4. "communication_style": How they typically express themselves
5. "decision_making_style": How they approach decisions
6. "typical_concerns": Common worries or priorities

Ensure the personality is internally consistent and reflects the demographic and psychological attributes provided.

Respond ONLY with valid JSON, no other text."""

    def validate_distribution(
        self,
        generated_personas: List[Dict[str, Any]],
        target_distribution: DemographicDistribution,
    ) -> Dict[str, Any]:
        """
        Validate that generated personas match target distribution using chi-square test
        Returns p-values for each demographic variable (should be > 0.05)
        """
        results = {}

        # Test age distribution (only if provided)
        if target_distribution.age_groups:
            results["age"] = self._chi_square_test(
                generated_personas, "age_group", target_distribution.age_groups
            )

        # Test gender distribution (only if provided)
        if target_distribution.genders:
            results["gender"] = self._chi_square_test(
                generated_personas, "gender", target_distribution.genders
            )

        # Test education distribution (only if provided)
        if target_distribution.education_levels:
            results["education"] = self._chi_square_test(
                generated_personas, "education_level", target_distribution.education_levels
            )

        # Test income distribution (only if provided)
        if target_distribution.income_brackets:
            results["income"] = self._chi_square_test(
                generated_personas, "income_bracket", target_distribution.income_brackets
            )

        # Test location distribution (only if provided)
        if target_distribution.locations:
            results["location"] = self._chi_square_test(
                generated_personas, "location", target_distribution.locations
            )

        # Overall validation
        all_p_values = [r["p_value"] for r in results.values() if "p_value" in r]
        results["overall_valid"] = all(
            p > settings.STATISTICAL_SIGNIFICANCE_THRESHOLD for p in all_p_values
        ) if all_p_values else True

        return results

    def _chi_square_test(
        self, personas: List[Dict[str, Any]], field: str, expected_dist: Dict[str, float]
    ) -> Dict[str, float]:
        """Perform chi-square test for a specific demographic field"""
        # Filter categories with non-positive expected probabilities
        valid_categories = [
            (category, probability)
            for category, probability in expected_dist.items()
            if probability and probability > 0
        ]

        if not valid_categories:
            return {
                "chi_square_statistic": 0.0,
                "p_value": 1.0,
                "degrees_of_freedom": 0,
                "observed": {},
                "expected": {},
            }

        total_prob = sum(probability for _, probability in valid_categories)
        normalized_probs = {
            category: probability / total_prob for category, probability in valid_categories
        }

        observed_counts = {category: 0 for category in normalized_probs}
        valid_samples = 0
        for persona in personas:
            value = persona.get(field)
            if value in observed_counts:
                observed_counts[value] += 1
                valid_samples += 1

        if valid_samples == 0:
            return {
                "chi_square_statistic": 0.0,
                "p_value": 1.0,
                "degrees_of_freedom": len(observed_counts) - 1,
                "observed": observed_counts,
                "expected": {category: 0.0 for category in observed_counts},
            }

        expected_counts = {
            category: normalized_probs[category] * valid_samples
            for category in normalized_probs
        }

        observed = [observed_counts[category] for category in normalized_probs]
        expected = [expected_counts[category] for category in normalized_probs]

        chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)

        return {
            "chi_square_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "degrees_of_freedom": len(normalized_probs) - 1,
            "observed": observed_counts,
            "expected": expected_counts,
            "sample_size": valid_samples,
        }
