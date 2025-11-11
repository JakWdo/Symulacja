"""
Tests for DemographicsLoader - Polish, International, and Common demographics.
"""

import pytest
from unittest.mock import patch

from config.demographics_loader import (
    DemographicsConfig,
    PolandDemographics,
    InternationalDemographics,
    CommonDemographics,
    get_demographics_config,
)


class TestPolandDemographics:
    """Test Polish demographics loading and validation."""

    @pytest.fixture
    def demographics(self):
        """Get demographics config."""
        return get_demographics_config()

    def test_locations_loaded(self, demographics):
        """Test that Polish locations are loaded correctly."""
        assert isinstance(demographics.poland.locations, dict)
        assert len(demographics.poland.locations) > 0

        # Check major cities exist
        assert "Warszawa" in demographics.poland.locations
        assert "Kraków" in demographics.poland.locations
        assert "Wrocław" in demographics.poland.locations

        # Verify probabilities are floats
        assert isinstance(demographics.poland.locations["Warszawa"], float)
        assert 0.0 < demographics.poland.locations["Warszawa"] <= 1.0

    def test_locations_probabilities_sum(self, demographics):
        """Test that location probabilities sum to approximately 1.0."""
        total = sum(demographics.poland.locations.values())
        assert 0.99 <= total <= 1.01, f"Location probabilities sum to {total}, expected ~1.0"

    def test_male_names_loaded(self, demographics):
        """Test that Polish male names are loaded."""
        assert isinstance(demographics.poland.male_names, list)
        assert len(demographics.poland.male_names) > 0

        # Check popular Polish male names
        assert "Jan" in demographics.poland.male_names
        assert "Piotr" in demographics.poland.male_names
        assert "Tomasz" in demographics.poland.male_names

    def test_female_names_loaded(self, demographics):
        """Test that Polish female names are loaded."""
        assert isinstance(demographics.poland.female_names, list)
        assert len(demographics.poland.female_names) > 0

        # Check popular Polish female names
        assert "Anna" in demographics.poland.female_names
        assert "Maria" in demographics.poland.female_names
        assert "Katarzyna" in demographics.poland.female_names

    def test_surnames_loaded(self, demographics):
        """Test that Polish surnames are loaded."""
        assert isinstance(demographics.poland.surnames, list)
        assert len(demographics.poland.surnames) > 0

        # Check common Polish surnames
        assert "Kowalski" in demographics.poland.surnames
        assert "Nowak" in demographics.poland.surnames

    def test_occupations_loaded(self, demographics):
        """Test that Polish occupations are loaded with probabilities."""
        assert isinstance(demographics.poland.occupations, dict)
        assert len(demographics.poland.occupations) > 0

        # Check occupation structure
        for occupation, probability in demographics.poland.occupations.items():
            assert isinstance(occupation, str)
            assert isinstance(probability, float)
            assert 0.0 < probability <= 1.0

    def test_occupations_probabilities_sum(self, demographics):
        """Test that occupation probabilities sum to approximately 1.0."""
        total = sum(demographics.poland.occupations.values())
        assert 0.99 <= total <= 1.01, f"Occupation probabilities sum to {total}, expected ~1.0"

    def test_values_loaded(self, demographics):
        """Test that Polish cultural values are loaded."""
        assert isinstance(demographics.poland.values, list)
        assert len(demographics.poland.values) > 0

        # Check some common Polish values
        " ".join(demographics.poland.values)
        assert any("rodzina" in v.lower() for v in demographics.poland.values)

    def test_interests_loaded(self, demographics):
        """Test that Polish interests are loaded."""
        assert isinstance(demographics.poland.interests, list)
        assert len(demographics.poland.interests) > 0

    def test_income_brackets_loaded(self, demographics):
        """Test that income brackets are loaded with probabilities."""
        assert isinstance(demographics.poland.income_brackets, dict)
        assert len(demographics.poland.income_brackets) > 0

        # Verify structure
        for bracket, probability in demographics.poland.income_brackets.items():
            assert isinstance(bracket, str)
            assert isinstance(probability, float)
            assert 0.0 < probability <= 1.0

    def test_education_levels_loaded(self, demographics):
        """Test that education levels are loaded with probabilities."""
        assert isinstance(demographics.poland.education_levels, dict)
        assert len(demographics.poland.education_levels) > 0

        # Verify structure
        for level, probability in demographics.poland.education_levels.items():
            assert isinstance(level, str)
            assert isinstance(probability, float)
            assert 0.0 < probability <= 1.0

    def test_communication_styles_loaded(self, demographics):
        """Test that communication styles are loaded."""
        assert isinstance(demographics.poland.communication_styles, list)
        assert len(demographics.poland.communication_styles) > 0

    def test_decision_styles_loaded(self, demographics):
        """Test that decision styles are loaded."""
        assert isinstance(demographics.poland.decision_styles, list)
        assert len(demographics.poland.decision_styles) > 0


class TestInternationalDemographics:
    """Test international demographics loading and validation."""

    @pytest.fixture
    def demographics(self):
        """Get demographics config."""
        return get_demographics_config()

    def test_locations_loaded(self, demographics):
        """Test that international locations are loaded."""
        assert isinstance(demographics.international.locations, dict)
        assert len(demographics.international.locations) > 0

        # Check major international cities
        locations = list(demographics.international.locations.keys())
        assert len(locations) > 0

    def test_age_groups_loaded(self, demographics):
        """Test that age groups are loaded for international."""
        assert isinstance(demographics.international.age_groups, dict)
        assert len(demographics.international.age_groups) > 0

    def test_genders_loaded(self, demographics):
        """Test that genders are loaded for international."""
        assert isinstance(demographics.international.genders, dict)
        assert len(demographics.international.genders) > 0

    def test_education_levels_loaded(self, demographics):
        """Test that education levels are loaded for international."""
        assert isinstance(demographics.international.education_levels, dict)
        assert len(demographics.international.education_levels) > 0

    def test_income_brackets_loaded(self, demographics):
        """Test that income brackets are loaded for international."""
        assert isinstance(demographics.international.income_brackets, dict)
        assert len(demographics.international.income_brackets) > 0

    def test_occupations_loaded(self, demographics):
        """Test that occupations are loaded as list (uniform distribution)."""
        assert isinstance(demographics.international.occupations, list)
        assert len(demographics.international.occupations) > 0

    def test_values_loaded(self, demographics):
        """Test that Western values are loaded."""
        assert isinstance(demographics.international.values, list)
        assert len(demographics.international.values) > 0

    def test_interests_loaded(self, demographics):
        """Test that international interests are loaded."""
        assert isinstance(demographics.international.interests, list)
        assert len(demographics.international.interests) > 0

    def test_communication_styles_loaded(self, demographics):
        """Test that communication styles are loaded."""
        assert isinstance(demographics.international.communication_styles, list)
        assert len(demographics.international.communication_styles) > 0

    def test_decision_styles_loaded(self, demographics):
        """Test that decision styles are loaded."""
        assert isinstance(demographics.international.decision_styles, list)
        assert len(demographics.international.decision_styles) > 0

    def test_life_situations_loaded(self, demographics):
        """Test that life situations are loaded."""
        assert isinstance(demographics.international.life_situations, list)
        assert len(demographics.international.life_situations) > 0


class TestCommonDemographics:
    """Test common demographics loading and validation."""

    @pytest.fixture
    def demographics(self):
        """Get demographics config."""
        return get_demographics_config()

    def test_age_groups_loaded(self, demographics):
        """Test that age groups are loaded correctly."""
        assert isinstance(demographics.common.age_groups, dict)
        assert len(demographics.common.age_groups) > 0

        # Check standard age groups exist
        assert "18-24" in demographics.common.age_groups
        assert "25-34" in demographics.common.age_groups
        assert "35-44" in demographics.common.age_groups
        assert "45-54" in demographics.common.age_groups
        assert "55-64" in demographics.common.age_groups
        assert "65+" in demographics.common.age_groups

    def test_age_group_probabilities(self, demographics):
        """Test that age group probabilities are valid floats."""
        for age_group, probability in demographics.common.age_groups.items():
            assert isinstance(probability, float)
            assert 0.0 < probability <= 1.0, f"Age group {age_group} has invalid probability {probability}"

    def test_age_group_probabilities_sum_to_one(self, demographics):
        """Test that age group probabilities sum to approximately 1.0."""
        total = sum(demographics.common.age_groups.values())
        assert 0.99 <= total <= 1.01, f"Age group probabilities sum to {total}, expected ~1.0"

    def test_genders_loaded(self, demographics):
        """Test that genders are loaded correctly."""
        assert isinstance(demographics.common.genders, dict)
        assert len(demographics.common.genders) > 0

        # Check standard genders
        assert "Male" in demographics.common.genders
        assert "Female" in demographics.common.genders

    def test_genders_probabilities(self, demographics):
        """Test that gender probabilities are valid floats."""
        for gender, probability in demographics.common.genders.items():
            assert isinstance(probability, float)
            assert 0.0 < probability <= 1.0

    def test_genders_probabilities_sum_to_one(self, demographics):
        """Test that gender probabilities sum to approximately 1.0."""
        total = sum(demographics.common.genders.values())
        assert 0.99 <= total <= 1.01, f"Gender probabilities sum to {total}, expected ~1.0"

    def test_family_situations_loaded(self, demographics):
        """Test that family situations are loaded."""
        assert isinstance(demographics.common.family_situations, list)
        assert len(demographics.common.family_situations) > 0

        # Check common family situations exist
        " ".join(demographics.common.family_situations).lower()
        assert any("single" in s.lower() or "married" in s.lower() or "children" in s.lower()
                   for s in demographics.common.family_situations)

    def test_personality_traits_loaded(self, demographics):
        """Test that personality traits (Big Five) are loaded."""
        assert isinstance(demographics.common.personality_traits, list)
        assert len(demographics.common.personality_traits) > 0


class TestDemographicsConfigSingleton:
    """Test singleton pattern and caching."""

    def test_singleton_returns_same_instance(self):
        """Test that get_demographics_config() returns the same instance."""
        config1 = get_demographics_config()
        config2 = get_demographics_config()

        assert config1 is config2, "Singleton should return same instance"

    def test_singleton_caches_data(self):
        """Test that data is cached (not reloaded on second access)."""
        config1 = get_demographics_config()
        poland_locations1 = config1.poland.locations

        config2 = get_demographics_config()
        poland_locations2 = config2.poland.locations

        # Should be same object reference (cached)
        assert poland_locations1 is poland_locations2


class TestDemographicsConfigErrorHandling:
    """Test error handling and fallbacks."""

    @patch("config.demographics_loader.ConfigLoader.load_yaml")
    def test_poland_file_not_found_returns_empty(self, mock_load):
        """Test that missing poland.yaml returns empty PolandDemographics."""
        mock_load.side_effect = FileNotFoundError("poland.yaml not found")

        config = DemographicsConfig()

        # Should have empty demographics
        assert isinstance(config.poland, PolandDemographics)
        assert config.poland.locations == {}
        assert config.poland.male_names == []

    @patch("config.demographics_loader.ConfigLoader.load_yaml")
    def test_international_file_not_found_returns_empty(self, mock_load):
        """Test that missing international.yaml returns empty InternationalDemographics."""
        mock_load.side_effect = FileNotFoundError("international.yaml not found")

        config = DemographicsConfig()

        # Should have empty demographics
        assert isinstance(config.international, InternationalDemographics)
        assert config.international.locations == {}
        assert config.international.occupations == []

    @patch("config.demographics_loader.ConfigLoader.load_yaml")
    def test_common_file_not_found_returns_empty(self, mock_load):
        """Test that missing common.yaml returns empty CommonDemographics."""
        mock_load.side_effect = FileNotFoundError("common.yaml not found")

        config = DemographicsConfig()

        # Should have empty demographics
        assert isinstance(config.common, CommonDemographics)
        assert config.common.age_groups == {}
        assert config.common.genders == {}

    def test_dataclass_defaults(self):
        """Test that dataclass default values work correctly."""
        poland = PolandDemographics()

        assert poland.locations == {}
        assert poland.values == []
        assert poland.male_names == []

        international = InternationalDemographics()

        assert international.locations == {}
        assert international.occupations == []

        common = CommonDemographics()

        assert common.age_groups == {}
        assert common.genders == {}
