"""
Test podstawowych funkcjonalności persona generator

Testuje metody które nie wymagają LLM API calls:
- sample_big_five_traits()
- sample_cultural_dimensions()

Uruchom: PYTHONPATH=/Users/jakubwdowicz/market-research-saas python tests/manual/test_basic_generator.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain


def test_basic_functions():
    """Test basic generator functions"""
    print("=== TEST BASIC PERSONA GENERATOR FUNCTIONS ===\n")

    # Initialize generator
    print("1. Initializing PersonaGeneratorLangChain...")
    generator = PersonaGeneratorLangChain()
    print("   ✓ Generator initialized\n")

    # Test Big Five sampling
    print("2. Testing Big Five traits sampling...")
    for i in range(3):
        traits = generator.sample_big_five_traits()
        print(f"   Sample {i+1}:")
        for trait, value in traits.items():
            print(f"      {trait}: {value:.3f}")

        # Validate
        assert len(traits) == 5
        assert all(0 <= v <= 1 for v in traits.values())
        assert "openness" in traits
        assert "conscientiousness" in traits
        assert "extraversion" in traits
        assert "agreeableness" in traits
        assert "neuroticism" in traits
    print("   ✓ Big Five sampling works correctly\n")

    # Test Cultural Dimensions sampling
    print("3. Testing Cultural Dimensions sampling...")
    for i in range(3):
        dimensions = generator.sample_cultural_dimensions()
        print(f"   Sample {i+1}:")
        for dim, value in dimensions.items():
            print(f"      {dim}: {value:.3f}")

        # Validate
        assert len(dimensions) == 6
        assert all(0 <= v <= 1 for v in dimensions.values())
        assert "power_distance" in dimensions
        assert "individualism" in dimensions
        assert "masculinity" in dimensions
        assert "uncertainty_avoidance" in dimensions
        assert "long_term_orientation" in dimensions
        assert "indulgence" in dimensions
    print("   ✓ Cultural Dimensions sampling works correctly\n")

    # Test combined psychographic profile
    print("4. Testing combined psychographic profile...")
    psycho_profile = {
        **generator.sample_big_five_traits(),
        **generator.sample_cultural_dimensions()
    }
    print(f"   Total traits: {len(psycho_profile)}")
    print(f"   All values in [0,1]: {all(0 <= v <= 1 for v in psycho_profile.values())}")
    assert len(psycho_profile) == 11  # 5 Big Five + 6 Hofstede
    print("   ✓ Combined profile works correctly\n")

    print("=== ALL BASIC TESTS PASSED ===\n")
    print("NOTE: Comprehensive generation with LLM requires full API flow.")
    print("      Test it by generating personas through the API endpoint.\n")
    return True


if __name__ == "__main__":
    success = test_basic_functions()
    sys.exit(0 if success else 1)
