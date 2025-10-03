"""
Generator Person oparty na LangChain i Google Gemini

Ten moduł generuje realistyczne, statystycznie reprezentatywne persony
dla badań rynkowych przy użyciu Google Gemini przez framework LangChain.

Kluczowe funkcjonalności:
- Generowanie person zgodnie z zadanymi rozkładami demograficznymi
- Walidacja statystyczna przy użyciu testu chi-kwadrat
- Sampling cech osobowości (Big Five) i wymiarów kulturowych (Hofstede)
- Integracja z LangChain dla łatwej zmiany modelu LLM
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
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
    """
    Rozkład demograficzny populacji docelowej

    Każde pole to słownik mapujący kategorie na prawdopodobieństwa (sumujące się do 1.0)
    Przykład: {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2}
    """
    age_groups: Dict[str, float]        # Grupy wiekowe
    genders: Dict[str, float]           # Płeć
    education_levels: Dict[str, float]  # Poziomy edukacji
    income_brackets: Dict[str, float]   # Przedziały dochodowe
    locations: Dict[str, float]         # Lokalizacje geograficzne


class PersonaGeneratorLangChain:
    """
    Generator statystycznie reprezentatywnych person przy użyciu LangChain + Gemini

    Używa Google Gemini do generowania realistycznych profili person na podstawie
    zadanych rozkładów demograficznych i psychologicznych.
    """

    def __init__(self):
        """Inicjalizuj generator z konfiguracją LangChain i Gemini"""
        self.settings = settings
        self._rng = np.random.default_rng(self.settings.RANDOM_SEED)

        # Initialize LangChain Gemini LLM with higher temperature for diversity
        persona_model = getattr(settings, "PERSONA_GENERATION_MODEL", settings.DEFAULT_MODEL)

        self.llm = ChatGoogleGenerativeAI(
            model=persona_model,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.9,  # Increased from default for more creative/diverse personas
            max_tokens=settings.MAX_TOKENS,
            top_p=0.95,
            top_k=40,
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

    def sample_big_five_traits(self, personality_skew: Dict[str, float] = None) -> Dict[str, float]:
        """
        Sample Big Five personality traits from normal distributions.

        Args:
            personality_skew: Optional dict to skew distributions.
                              Keys: 'openness', 'conscientiousness', etc.
                              Values: 0.0-1.0 (mean shift: 0=low, 0.5=balanced, 1.0=high)
        """
        skew = personality_skew or {}

        traits = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            # Default mean = 0.5, std = 0.15
            mean = skew.get(trait, 0.5)
            # Ensure mean is valid
            mean = np.clip(mean, 0.0, 1.0)

            value = np.clip(self._rng.normal(mean, 0.15), 0, 1)
            traits[trait] = value

        return traits

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
        self, demographic_profile: Dict[str, Any], psychological_profile: Dict[str, Any], advanced_options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate persona personality using LangChain + Gemini"""

        prompt_text = self._create_persona_prompt(demographic_profile, psychological_profile)

        # Use LangChain chain to generate structured response
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(
                f"Generating persona with demographics: {demographic_profile.get('age_group')}, "
                f"{demographic_profile.get('gender')}, {demographic_profile.get('location')}"
            )
            response = await self.persona_chain.ainvoke({"prompt": prompt_text})

            # Log response for debugging
            logger.info(f"LLM response type: {type(response)}, keys: {response.keys() if isinstance(response, dict) else 'N/A'}")

            # Validate required fields
            required_fields = ["full_name", "persona_title", "headline", "background_story", "values", "interests"]
            missing_fields = [field for field in required_fields if not response.get(field)]
            if missing_fields:
                logger.error(
                    f"LLM response missing required fields: {missing_fields}. "
                    f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'NOT A DICT'}"
                )

            return prompt_text, response
        except Exception as e:
            logger.error(f"Failed to generate persona: {str(e)[:500]}", exc_info=True)
            # Fallback for parsing errors
            raise ValueError(f"Failed to generate persona: {str(e)}")

    def _create_persona_prompt(
        self, demographic: Dict[str, Any], psychological: Dict[str, Any]
    ) -> str:
        """Create prompt for LLM persona generation with few-shot examples and trait guidance"""

        # Generate unique seed for this persona
        persona_seed = self._rng.integers(1000, 9999)

        # Trait interpretation guidance
        openness_val = psychological.get('openness', 0.5)
        conscientiousness_val = psychological.get('conscientiousness', 0.5)
        extraversion_val = psychological.get('extraversion', 0.5)
        agreeableness_val = psychological.get('agreeableness', 0.5)
        neuroticism_val = psychological.get('neuroticism', 0.5)

        openness_hint = "creative, curious, open to new experiences" if openness_val > 0.6 else "practical, traditional, prefers routine" if openness_val < 0.4 else "moderately adventurous"
        conscientiousness_hint = "organized, disciplined, detail-oriented" if conscientiousness_val > 0.6 else "spontaneous, flexible, less structured" if conscientiousness_val < 0.4 else "balanced planning style"
        extraversion_hint = "outgoing, energetic, social" if extraversion_val > 0.6 else "reserved, introspective, prefers solitude" if extraversion_val < 0.4 else "ambivert"
        agreeableness_hint = "cooperative, compassionate, empathetic" if agreeableness_val > 0.6 else "competitive, direct, skeptical" if agreeableness_val < 0.4 else "balanced social approach"
        neuroticism_hint = "anxious, sensitive, stress-prone" if neuroticism_val > 0.6 else "calm, resilient, emotionally stable" if neuroticism_val < 0.4 else "moderately emotional"

        return f"""You are a world-class market research expert creating synthetic personas for behavioral research. Your personas must be UNIQUE, REALISTIC, and INTERNALLY CONSISTENT.

PERSONA #{persona_seed}

DEMOGRAPHICS:
- Age Group: {demographic.get('age_group')}
- Gender: {demographic.get('gender')}
- Education: {demographic.get('education_level')}
- Income: {demographic.get('income_bracket')}
- Location: {demographic.get('location')}

PERSONALITY TRAITS (Big Five):
- Openness: {openness_val:.2f} → {openness_hint}
- Conscientiousness: {conscientiousness_val:.2f} → {conscientiousness_hint}
- Extraversion: {extraversion_val:.2f} → {extraversion_hint}
- Agreeableness: {agreeableness_val:.2f} → {agreeableness_hint}
- Neuroticism: {neuroticism_val:.2f} → {neuroticism_hint}

CULTURAL DIMENSIONS (Hofstede):
- Power Distance: {psychological.get('power_distance', 0.5):.2f}
- Individualism: {psychological.get('individualism', 0.5):.2f}
- Uncertainty Avoidance: {psychological.get('uncertainty_avoidance', 0.5):.2f}

CRITICAL INSTRUCTIONS FOR DIVERSITY:
1. Make this persona DISTINCTIVE - avoid generic descriptions
2. Age matters: 25yo and 65yo have VERY different life contexts
3. Occupation must align with education level and income
4. Background story must reflect personality traits:
   - High Openness → travel, creative hobbies, diverse experiences
   - High Conscientiousness → structured career path, planning
   - High Extraversion → social activities, networking
   - Low Agreeableness → competitive fields, independent work
   - High Individualism → entrepreneurial, self-reliant
5. Be specific with details (actual city neighborhoods, specific brands, real activities)

FEW-SHOT EXAMPLES:

Example 1 (High Openness, Mid-career professional):
{{
  "full_name": "Maya Chen",
  "persona_title": "Freelance UX Designer",
  "headline": "Brooklyn-based UX designer experimenting with AR storytelling for museums.",
  "background_story": "Maya is a 34-year-old UX designer in Brooklyn who left corporate life to freelance after a transformative trip to Japan. She's currently learning Japanese and building a side project exploring AR interfaces for museums. Single and loving the freedom to take on diverse clients from sustainable fashion to educational tech startups.",
  "values": ["Creativity", "Autonomy", "Continuous Learning", "Authenticity", "Sustainability"],
  "interests": ["Japanese language", "AR/VR Design", "Sustainable Fashion", "Museum Visits", "Meditation", "Urban Sketching"],
  "communication_style": "enthusiastic and visual, often uses metaphors and examples from diverse fields",
  "decision_making_style": "intuition-based with research; tests ideas quickly through prototypes",
  "typical_concerns": ["Maintaining creative freedom while ensuring financial stability", "Finding meaningful client work", "Balancing solo work with social connection"]
}}

Example 2 (Low Openness, High Conscientiousness, approaching retirement):
{{
  "full_name": "Robert Hayes",
  "persona_title": "Veteran Financial Advisor",
  "headline": "Dallas advisor meticulously planning retirement while mentoring the next generation.",
  "background_story": "Robert is a 58-year-old financial advisor in Dallas who has worked at the same firm for 32 years. Married with two grown children, he's meticulously planning his retirement and recently purchased a lake house. He serves as treasurer of his local Rotary Club and takes pride in his predictable routine and extensive client relationships built over decades.",
  "values": ["Stability", "Loyalty", "Family", "Responsibility", "Tradition", "Integrity"],
  "interests": ["Golf", "Classic Cars", "Financial Planning Podcasts", "Grilling", "Rotary Club", "Lake Fishing"],
  "communication_style": "formal and professional, prefers face-to-face meetings, uses established frameworks",
  "decision_making_style": "methodical and risk-averse, relies on proven methods and extensive planning",
  "typical_concerns": ["Ensuring sufficient retirement savings", "Maintaining client relationships through succession", "Health insurance in retirement", "Legacy planning for children"]
}}

Example 3 (High Extraversion, High Neuroticism, recent graduate):
{{
  "full_name": "Jasmine Ortiz",
  "persona_title": "Social Media Manager & Creator",
  "headline": "Gen-Z marketer hustling in LA's creator economy while navigating early-career anxiety.",
  "background_story": "Jasmine is a 23-year-old social media manager in Los Angeles who recently graduated with a marketing degree. She juggles anxiety about job security with excitement for the creator economy. Living with three roommates in Echo Park, she's always networking at industry events while building her personal brand as a Gen-Z marketing consultant. She's close to her immigrant parents who don't fully understand her career choice.",
  "values": ["Connection", "Recognition", "Authenticity", "Innovation", "Family", "Success"],
  "interests": ["TikTok Content Creation", "Networking Events", "Brunch Culture", "Thrifting", "Podcast Listening", "Mental Health Advocacy", "K-pop"],
  "communication_style": "energetic and trend-aware, uses social media vernacular, highly expressive",
  "decision_making_style": "impulsive but collaborative, seeks validation from peers before committing",
  "typical_concerns": ["Job security in volatile industry", "Student loan debt", "Comparison anxiety from social media", "Proving career choice to family", "Building sustainable income"]
}}

Now generate a COMPLETELY DIFFERENT persona following the same level of specificity and consistency with the provided demographic and psychological profile.

Generate JSON ONLY (no markdown, no extra text):
{{
  "full_name": "<realistic first and last name aligned with location>",
  "persona_title": "<concise professional or life-stage title>",
  "headline": "<one sentence summary consistent with age, occupation, and motivations>",
  "background_story": "<2-3 specific sentences about their current life, career trajectory, and unique context>",
  "values": ["<5-7 specific values that drive their decisions>"],
  "interests": ["<5-7 specific hobbies/activities they actually do>"],
  "communication_style": "<how they express themselves>",
  "decision_making_style": "<how they approach important choices>",
  "typical_concerns": ["<3-5 specific worries or priorities in their current life stage>"]
}}"""

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
