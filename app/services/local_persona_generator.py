"""Offline persona generator for when LLM providers are unavailable."""
import random
from typing import Any, Dict, List, Tuple

from app.services import DemographicDistribution
from app.core.constants import DEFAULT_VALUES, DEFAULT_INTERESTS


class LocalPersonaSynthesizer:
    """Offline persona generator using random sampling."""

    def __init__(self) -> None:
        self._rng = random.Random()

    def sample_demographic_profile(
        self, distribution: DemographicDistribution, n_samples: int = 1
    ) -> List[Dict[str, Any]]:
        """Sample demographic profiles from given distributions."""
        def weighted_sample(options: Dict[str, float]) -> str:
            if not options:
                raise ValueError("distribution missing choices")
            keys = list(options.keys())
            weights = list(options.values())
            return random.choices(keys, weights=weights, k=1)[0]

        profiles: List[Dict[str, Any]] = []
        for _ in range(n_samples):
            profiles.append(
                {
                    "age_group": weighted_sample(distribution.age_groups),
                    "gender": weighted_sample(distribution.genders),
                    "education_level": weighted_sample(distribution.education_levels),
                    "income_bracket": weighted_sample(distribution.income_brackets),
                    "location": weighted_sample(distribution.locations),
                }
            )
        return profiles

    def sample_big_five_traits(self) -> Dict[str, float]:
        """Sample Big Five personality traits."""
        return {
            "openness": self._bounded_gauss(0.55, 0.18),
            "conscientiousness": self._bounded_gauss(0.52, 0.2),
            "extraversion": self._bounded_gauss(0.5, 0.22),
            "agreeableness": self._bounded_gauss(0.58, 0.17),
            "neuroticism": self._bounded_gauss(0.45, 0.2),
        }

    def sample_cultural_dimensions(self) -> Dict[str, float]:
        """Sample Hofstede cultural dimensions."""
        return {
            "power_distance": self._bounded_gauss(0.48, 0.25),
            "individualism": self._bounded_gauss(0.52, 0.24),
            "masculinity": self._bounded_gauss(0.49, 0.23),
            "uncertainty_avoidance": self._bounded_gauss(0.51, 0.22),
            "long_term_orientation": self._bounded_gauss(0.55, 0.21),
            "indulgence": self._bounded_gauss(0.47, 0.26),
        }

    async def generate_persona_personality(
        self, demographic_profile: Dict[str, Any], psychological_profile: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate synthetic persona personality."""
        prompt = "offline-synthesized-persona"
        name_seed = self._rng.choice([
            "Alex",
            "Jordan",
            "Taylor",
            "Morgan",
            "Casey",
            "Riley",
            "Jamie",
        ])
        lifestyle_focus = self._rng.choice([
            "balancing career growth with personal wellbeing",
            "adopting sustainable routines at home",
            "exploring side projects and entrepreneurial ideas",
            "prioritising community-driven initiatives",
            "navigating major life transitions with optimism",
        ])
        personality = {
            "background_story": (
                f"{name_seed} lives in {demographic_profile.get('location', 'a mid-sized city')} and is"
                f" focused on {lifestyle_focus}. They enjoy connecting with peers who share similar"
                " ambitions and values."
            ),
            "values": random.sample(DEFAULT_VALUES, k=min(4, len(DEFAULT_VALUES))),
            "interests": random.sample(
                DEFAULT_INTERESTS, k=min(4, len(DEFAULT_INTERESTS))
            ),
            "communication_style": self._rng.choice(
                [
                    "direct and pragmatic",
                    "empathetic and story-driven",
                    "data-informed with collaborative tone",
                    "enthusiastic and forward-looking",
                ]
            ),
            "decision_making_style": self._rng.choice(
                [
                    "balances instinct with available research",
                    "consults trusted peers before acting",
                    "tests ideas quickly and iterates",
                    "prefers structured frameworks and planning",
                ]
            ),
            "typical_concerns": [
                "staying relevant in a fast-changing market",
                "maintaining authenticity when scaling efforts",
                "aligning personal goals with community impact",
            ],
        }
        return prompt, personality

    def _bounded_gauss(self, mean: float, std: float) -> float:
        """Sample from Gaussian distribution bounded to [0, 1]."""
        value = self._rng.gauss(mean, std)
        return max(0.0, min(1.0, value))
