"""
Test end-to-end dla comprehensive persona generation

Ten skrypt testuje:
1. Czy comprehensive generation działa bez błędów
2. Czy wszystkie wymagane pola są wypełnione
3. Czy dane są spójne (demographics, psychographics, content)

Uruchom: PYTHONPATH=/Users/jakubwdowicz/market-research-saas python tests/manual/test_comprehensive_generation.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.personas.persona_generator_langchain import PersonaGeneratorLangChain


async def test_comprehensive_generation():
    """Test comprehensive persona generation"""
    print("=== TEST COMPREHENSIVE PERSONA GENERATION ===\n")

    # Initialize generator
    print("1. Initializing PersonaGeneratorLangChain...")
    generator = PersonaGeneratorLangChain()
    print("   ✓ Generator initialized\n")

    # Test data
    orchestration_brief = """
    Ten segment obejmuje młodych profesjonalistów (25-34 lata) z wyższym wykształceniem,
    pracujących w branży IT w dużych miastach. Charakteryzują się wysoką adaptacyjnością
    technologiczną, cenią work-life balance i rozwój zawodowy.
    """

    segment_characteristics = [
        "Wysoka znajomość technologii",
        "Ambicja zawodowa",
        "Mobilność geograficzna",
        "Świadomość ekologiczna"
    ]

    demographic_guidance = {
        "age": "25-34",
        "gender": "Kobieta",
        "location": "Warszawa",
        "education_level": "Wyższe magisterskie",
        "income_bracket": "7 500 - 10 000 zł"
    }

    # Sample psychographics
    psychological_profile = {
        **generator.sample_big_five_traits(),
        **generator.sample_cultural_dimensions()
    }

    print("2. Test parameters:")
    print(f"   Brief: {orchestration_brief[:80]}...")
    print(f"   Characteristics: {len(segment_characteristics)} items")
    print(f"   Demographics: {demographic_guidance['age']}, {demographic_guidance['gender']}")
    print()

    # Generate persona
    print("3. Generating comprehensive persona...")
    try:
        persona_data = await generator.generate_comprehensive_persona(
            orchestration_brief=orchestration_brief,
            segment_characteristics=segment_characteristics,
            demographic_guidance=demographic_guidance,
            rag_context=None,
            psychological_profile=psychological_profile
        )
        print("   ✓ Generation successful\n")
    except Exception as e:
        print(f"   ✗ Generation FAILED: {e}\n")
        return False

    # Validate required fields
    print("4. Validating required fields...")
    required_fields = [
        "full_name",
        "occupation",
        "age",
        "gender",
        "location",
        "education_level",
        "income_bracket",
        "background_story",
        "values",
        "interests"
    ]

    missing_fields = []
    for field in required_fields:
        if field not in persona_data or not persona_data[field]:
            missing_fields.append(field)

    if missing_fields:
        print(f"   ✗ Missing fields: {', '.join(missing_fields)}\n")
        return False
    else:
        print("   ✓ All required fields present\n")

    # Display generated persona
    print("5. Generated Persona:")
    print(f"   Name: {persona_data['full_name']}")
    print(f"   Age: {persona_data['age']}")
    print(f"   Gender: {persona_data['gender']}")
    print(f"   Location: {persona_data['location']}")
    print(f"   Education: {persona_data['education_level']}")
    print(f"   Income: {persona_data['income_bracket']}")
    print(f"   Occupation: {persona_data['occupation']}")
    print(f"   Background: {persona_data['background_story'][:100]}...")
    print(f"   Values ({len(persona_data['values'])}): {', '.join(persona_data['values'][:3])}")
    print(f"   Interests ({len(persona_data['interests'])}): {', '.join(persona_data['interests'][:3])}")
    print()

    # Validate psychographics were added
    print("6. Validating psychographics...")
    psycho_fields = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    missing_psycho = [f for f in psycho_fields if f not in persona_data]

    if missing_psycho:
        print(f"   ✗ Missing psychographics: {', '.join(missing_psycho)}\n")
        return False
    else:
        print("   ✓ All psychographic traits present\n")

    # Check data quality
    print("7. Data quality checks:")

    # Check if name looks Polish
    if any(char in persona_data['full_name'] for char in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'):
        print("   ✓ Name has Polish characters")
    else:
        print(f"   ⚠  Name '{persona_data['full_name']}' doesn't look Polish")

    # Check if age is within demographic_guidance range
    age_range = demographic_guidance['age']
    if '-' in age_range:
        min_age, max_age = map(int, age_range.split('-'))
        if min_age <= persona_data['age'] <= max_age:
            print(f"   ✓ Age {persona_data['age']} is within guidance range {age_range}")
        else:
            print(f"   ⚠  Age {persona_data['age']} outside guidance range {age_range}")

    # Check values and interests are lists
    if isinstance(persona_data['values'], list) and len(persona_data['values']) >= 3:
        print(f"   ✓ Values list has {len(persona_data['values'])} items")
    else:
        print(f"   ⚠  Values list insufficient: {persona_data['values']}")

    if isinstance(persona_data['interests'], list) and len(persona_data['interests']) >= 3:
        print(f"   ✓ Interests list has {len(persona_data['interests'])} items")
    else:
        print(f"   ⚠  Interests list insufficient: {persona_data['interests']}")

    print("\n=== TEST COMPLETED SUCCESSFULLY ===\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_generation())
    sys.exit(0 if success else 1)
