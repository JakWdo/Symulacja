import pytest
import numpy as np
from app.services.persona_generator import PersonaGenerator, DemographicDistribution


@pytest.fixture
def sample_distribution():
    """Sample demographic distribution for testing"""
    return DemographicDistribution(
        age_groups={"18-24": 0.15, "25-34": 0.25, "35-44": 0.25, "45-54": 0.20, "55+": 0.15},
        genders={"male": 0.49, "female": 0.51},
        education_levels={
            "high_school": 0.30,
            "bachelors": 0.40,
            "masters": 0.20,
            "phd": 0.10,
        },
        income_brackets={
            "<30k": 0.20,
            "30k-60k": 0.30,
            "60k-100k": 0.30,
            "100k+": 0.20,
        },
        locations={"urban": 0.60, "suburban": 0.30, "rural": 0.10},
    )


@pytest.fixture
def generator():
    """PersonaGenerator instance"""
    return PersonaGenerator()


def test_weighted_sampling(generator, sample_distribution):
    """Test that weighted sampling respects distributions"""
    samples = []
    for _ in range(1000):
        sample = generator._weighted_sample(sample_distribution.age_groups)
        samples.append(sample)

    # Check that all categories are represented
    unique_values = set(samples)
    assert unique_values == set(sample_distribution.age_groups.keys())

    # Check proportions (with some tolerance)
    for category, expected_prob in sample_distribution.age_groups.items():
        observed_prob = samples.count(category) / len(samples)
        assert abs(observed_prob - expected_prob) < 0.05  # 5% tolerance


def test_sample_demographic_profile(generator, sample_distribution):
    """Test demographic profile sampling"""
    profiles = generator.sample_demographic_profile(sample_distribution, n_samples=10)

    assert len(profiles) == 10

    for profile in profiles:
        assert "age_group" in profile
        assert "gender" in profile
        assert "education_level" in profile
        assert "income_bracket" in profile
        assert "location" in profile

        assert profile["age_group"] in sample_distribution.age_groups
        assert profile["gender"] in sample_distribution.genders
        assert profile["education_level"] in sample_distribution.education_levels
        assert profile["income_bracket"] in sample_distribution.income_brackets
        assert profile["location"] in sample_distribution.locations


def test_big_five_traits_sampling(generator):
    """Test Big Five personality trait sampling"""
    traits = generator.sample_big_five_traits()

    assert "openness" in traits
    assert "conscientiousness" in traits
    assert "extraversion" in traits
    assert "agreeableness" in traits
    assert "neuroticism" in traits

    # All traits should be between 0 and 1
    for trait_value in traits.values():
        assert 0 <= trait_value <= 1


def test_cultural_dimensions_sampling(generator):
    """Test Hofstede cultural dimensions sampling"""
    dimensions = generator.sample_cultural_dimensions()

    expected_dimensions = [
        "power_distance",
        "individualism",
        "masculinity",
        "uncertainty_avoidance",
        "long_term_orientation",
        "indulgence",
    ]

    for dim in expected_dimensions:
        assert dim in dimensions
        assert 0 <= dimensions[dim] <= 1


def test_chi_square_validation(generator, sample_distribution):
    """Test chi-square statistical validation"""
    # Generate personas that match distribution
    personas = []
    for _ in range(200):
        profile = generator.sample_demographic_profile(sample_distribution)[0]
        personas.append(profile)

    # Validate distribution
    validation = generator.validate_distribution(personas, sample_distribution)

    # Check structure
    assert "age" in validation
    assert "gender" in validation
    assert "education" in validation
    assert "income" in validation
    assert "location" in validation
    assert "overall_valid" in validation

    # Each test should have p_value
    for key in ["age", "gender", "education", "income", "location"]:
        assert "p_value" in validation[key]
        assert "chi_square_statistic" in validation[key]
        assert "degrees_of_freedom" in validation[key]

    # With 200 samples, distribution should be valid (p > 0.05)
    assert validation["overall_valid"] is True


def test_chi_square_validation_small_sample(generator, sample_distribution):
    """Test chi-square with insufficient sample size"""
    # Generate only 20 personas (too small for good statistical validation)
    personas = []
    for _ in range(20):
        profile = generator.sample_demographic_profile(sample_distribution)[0]
        personas.append(profile)

    validation = generator.validate_distribution(personas, sample_distribution)

    # Structure should still be correct
    assert "overall_valid" in validation

    # With small sample, might fail validation (that's expected)
    # Just verify the test completes without error