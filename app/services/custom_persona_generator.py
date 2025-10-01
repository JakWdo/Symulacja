"""
Custom Persona Generator with advanced filtering and targeting
Extends PersonaGeneratorLangChain with custom demographic/psychographic constraints
"""

import random
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.config import get_settings
from app.core.constants import (
    DEFAULT_AGE_GROUPS,
    DEFAULT_GENDERS,
    DEFAULT_EDUCATION_LEVELS,
    DEFAULT_INCOME_BRACKETS,
    DEFAULT_LOCATIONS,
    DEFAULT_OCCUPATIONS,
    DEFAULT_VALUES,
    DEFAULT_INTERESTS,
)
from app.services.persona_generator_langchain import (
    PersonaGeneratorLangChain,
    DemographicDistribution,
)

settings = get_settings()


class CustomPersonaGenerator(PersonaGeneratorLangChain):
    """
    Extended persona generator with custom demographic and psychographic targeting
    """

    def __init__(self):
        super().__init__()
        self._rng = np.random.default_rng(settings.RANDOM_SEED)

    def apply_custom_distribution(
        self,
        base_distribution: DemographicDistribution,
        custom_demographics: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> DemographicDistribution:
        """
        Apply custom demographic distributions on top of base distribution
        """
        if not custom_demographics:
            return base_distribution

        return DemographicDistribution(
            age_groups=self._prepare_distribution(
                custom_demographics.get("age_groups", {}),
                base_distribution.age_groups,
            ),
            genders=self._prepare_distribution(
                custom_demographics.get("genders", {}), base_distribution.genders
            ),
            education_levels=self._prepare_distribution(
                custom_demographics.get("education_levels", {}),
                base_distribution.education_levels,
            ),
            income_brackets=self._prepare_distribution(
                custom_demographics.get("income_brackets", {}),
                base_distribution.income_brackets,
            ),
            locations=self._prepare_distribution(
                custom_demographics.get("locations", {}),
                base_distribution.locations,
            ),
        )

    def filter_by_geography(
        self,
        demographic: Dict[str, Any],
        countries: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        urban_rural_ratio: Optional[float] = None,
    ) -> bool:
        """
        Check if demographic profile matches geographic constraints
        Returns True if profile passes filters
        """
        location = demographic.get("location", "")

        # Country filter
        if countries:
            # Simple heuristic: assume US locations by default
            if "United States" not in countries and location:
                return False

        # State filter
        if states and location:
            location_parts = location.split(",")
            state = location_parts[1].strip() if len(location_parts) > 1 else ""
            if not any(s.upper() in state.upper() for s in states):
                return False

        # City filter
        if cities and location:
            city = location.split(",")[0].strip()
            if not any(c.upper() in city.upper() for c in cities):
                return False

        # Urban/rural ratio (simplified: major cities = urban)
        if urban_rural_ratio is not None:
            major_cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
            is_urban = any(city in location for city in major_cities)
            if urban_rural_ratio > 0.7 and not is_urban:
                return False
            if urban_rural_ratio < 0.3 and is_urban:
                return False

        return True

    def apply_psychographic_filters(
        self,
        personality: Dict[str, Any],
        required_values: Optional[List[str]] = None,
        excluded_values: Optional[List[str]] = None,
        required_interests: Optional[List[str]] = None,
        excluded_interests: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Apply psychographic filters and adjust personality accordingly
        """
        values = set(personality.get("values", []))
        interests = set(personality.get("interests", []))

        # Apply required values
        if required_values:
            missing_values = set(required_values) - values
            if missing_values:
                # Add required values, remove random ones if needed
                values.update(missing_values)
                while len(values) > 7:  # Max 7 values
                    removable = values - set(required_values)
                    if removable:
                        values.remove(random.choice(list(removable)))

        # Remove excluded values
        if excluded_values:
            values -= set(excluded_values)

        # Apply required interests
        if required_interests:
            missing_interests = set(required_interests) - interests
            if missing_interests:
                interests.update(missing_interests)
                while len(interests) > 10:  # Max 10 interests
                    removable = interests - set(required_interests)
                    if removable:
                        interests.remove(random.choice(list(removable)))

        # Remove excluded interests
        if excluded_interests:
            interests -= set(excluded_interests)

        # Ensure minimum values/interests
        if len(values) < 3:
            available_values = set(DEFAULT_VALUES) - values - set(excluded_values or [])
            values.update(random.sample(list(available_values), min(3 - len(values), len(available_values))))

        if len(interests) < 3:
            available_interests = set(DEFAULT_INTERESTS) - interests - set(excluded_interests or [])
            interests.update(
                random.sample(list(available_interests), min(3 - len(interests), len(available_interests)))
            )

        personality["values"] = list(values)
        personality["interests"] = list(interests)
        return personality

    def apply_occupation_filter(
        self,
        occupation: str,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Filter occupation based on whitelist/blacklist/industries
        Returns filtered occupation or None if doesn't match
        """
        if blacklist and any(b.lower() in occupation.lower() for b in blacklist):
            return None

        if whitelist and not any(w.lower() in occupation.lower() for w in whitelist):
            # Try to find alternative from whitelist
            return random.choice(whitelist) if whitelist else None

        # Industry filtering (simplified keyword matching)
        if industries:
            industry_keywords = {
                "Tech": ["Software", "Data", "Engineer", "Developer", "IT", "Cloud", "Cybersecurity"],
                "Healthcare": ["Physician", "Nurse", "Doctor", "Medical", "Healthcare"],
                "Finance": ["Financial", "Banker", "Accountant", "Analyst"],
                "Education": ["Teacher", "Professor", "Educator", "Instructor"],
                "Creative": ["Designer", "Artist", "Writer", "Photographer", "Creative"],
            }

            occupation_matches_industry = False
            for industry in industries:
                keywords = industry_keywords.get(industry, [])
                if any(kw.lower() in occupation.lower() for kw in keywords):
                    occupation_matches_industry = True
                    break

            if not occupation_matches_industry:
                # Try to find occupation from desired industry
                for industry in industries:
                    keywords = industry_keywords.get(industry, [])
                    matching_occupations = [
                        occ for occ in DEFAULT_OCCUPATIONS
                        if any(kw.lower() in occ.lower() for kw in keywords)
                    ]
                    if matching_occupations:
                        return random.choice(matching_occupations)

        return occupation

    def adjust_personality_to_target(
        self,
        psychological: Dict[str, float],
        targets: Optional[Dict[str, float]] = None,
        personality_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> Dict[str, float]:
        """
        Adjust psychological traits to match target values or ranges
        """
        if targets:
            for trait, target_value in targets.items():
                if trait in psychological:
                    # Blend current value with target (70% target, 30% original for diversity)
                    current = psychological[trait]
                    psychological[trait] = np.clip(
                        target_value * 0.7 + current * 0.3, 0.0, 1.0
                    )

        if personality_ranges:
            for trait, (min_val, max_val) in personality_ranges.items():
                if trait in psychological:
                    # Ensure trait falls within range
                    current = psychological[trait]
                    if current < min_val:
                        psychological[trait] = np.clip(
                            self._rng.uniform(min_val, min_val + 0.15), 0.0, 1.0
                        )
                    elif current > max_val:
                        psychological[trait] = np.clip(
                            self._rng.uniform(max_val - 0.15, max_val), 0.0, 1.0
                        )

        return psychological

    def override_age_range(
        self,
        demographic: Dict[str, Any],
        age_range: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Override age with custom range
        """
        if not age_range:
            return demographic

        min_age, max_age = age_range
        new_age = self._rng.integers(min_age, max_age + 1)

        # Update age group
        if new_age < 25:
            age_group = "18-24"
        elif new_age < 35:
            age_group = "25-34"
        elif new_age < 45:
            age_group = "35-44"
        elif new_age < 55:
            age_group = "45-54"
        elif new_age < 65:
            age_group = "55-64"
        else:
            age_group = "65+"

        demographic["age"] = new_age
        demographic["age_group"] = age_group
        return demographic

    async def generate_custom_persona(
        self,
        base_distribution: DemographicDistribution,
        custom_demographics: Optional[Dict[str, Dict[str, float]]] = None,
        geographic_constraints: Optional[Dict[str, Any]] = None,
        psychographic_targets: Optional[Dict[str, Any]] = None,
        occupation_filter: Optional[Dict[str, Any]] = None,
        age_range_override: Optional[Tuple[int, int]] = None,
        cultural_dimensions_target: Optional[Dict[str, float]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Generate a single persona with custom constraints
        Returns: (demographic, psychological, prompt)
        """
        # Apply custom distributions
        distribution = self.apply_custom_distribution(
            base_distribution, custom_demographics
        )

        # Sample demographic profile
        max_attempts = 50
        demographic = None
        for _ in range(max_attempts):
            demo_sample = self.sample_demographic_profile(distribution, n_samples=1)[0]

            # Apply geographic filters
            if geographic_constraints:
                if not self.filter_by_geography(demo_sample, **geographic_constraints):
                    continue

            demographic = demo_sample
            break

        if not demographic:
            # Fallback to unfiltered sample
            demographic = self.sample_demographic_profile(distribution, n_samples=1)[0]

        # Override age if needed
        if age_range_override:
            demographic = self.override_age_range(demographic, age_range_override)

        # Sample psychological traits
        psychological = self.sample_big_five_traits()
        cultural = self.sample_cultural_dimensions()
        psychological.update(cultural)

        # Adjust to cultural targets
        if cultural_dimensions_target:
            psychological = self.adjust_personality_to_target(
                psychological, targets=cultural_dimensions_target
            )

        # Adjust to personality ranges
        if psychographic_targets and psychographic_targets.get("personality_ranges"):
            psychological = self.adjust_personality_to_target(
                psychological,
                personality_ranges=psychographic_targets["personality_ranges"],
            )

        # Generate personality with LLM
        prompt, personality = await self.generate_persona_personality(
            demographic, psychological
        )

        # Apply psychographic filters
        if psychographic_targets:
            personality = self.apply_psychographic_filters(
                personality,
                required_values=psychographic_targets.get("required_values"),
                excluded_values=psychographic_targets.get("excluded_values"),
                required_interests=psychographic_targets.get("required_interests"),
                excluded_interests=psychographic_targets.get("excluded_interests"),
            )

        # Apply occupation filter
        if occupation_filter:
            occupation = personality.get("occupation") or demographic.get("occupation")
            if occupation:
                filtered_occupation = self.apply_occupation_filter(
                    occupation,
                    whitelist=occupation_filter.get("whitelist"),
                    blacklist=occupation_filter.get("blacklist"),
                    industries=occupation_filter.get("industries"),
                )
                if filtered_occupation:
                    personality["occupation"] = filtered_occupation

        return demographic, psychological, prompt, personality
