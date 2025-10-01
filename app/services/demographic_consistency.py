"""
Demographic consistency helpers for ensuring persona attributes align logically
"""
import random
from typing import Dict, Optional

# Occupation tiers based on typical education requirements
EDUCATION_OCCUPATION_MAP = {
    "High school": [
        "Retail Manager", "Customer Service Manager", "Restaurant Manager",
        "Electrician", "Plumber", "Carpenter", "Mechanic", "HVAC Technician",
        "Construction Manager", "Real Estate Agent", "Chef", "Personal Trainer",
    ],
    "Some college": [
        "Retail Manager", "Marketing Specialist", "Social Media Manager",
        "Graphic Designer", "Video Editor", "Customer Success Manager",
        "Restaurant Manager", "Event Planner", "Real Estate Agent",
        "Electrician", "Plumber", "Carpenter", "Personal Trainer", "Life Coach",
    ],
    "Bachelor's degree": [
        "Software Engineer", "Product Manager", "UX Designer", "Data Analyst",
        "Marketing Manager", "Business Analyst", "Project Manager",
        "Account Executive", "Brand Strategist", "Content Creator",
        "Teacher", "Financial Analyst", "Accountant", "Journalist",
        "Social Worker", "Photographer", "Interior Designer",
    ],
    "Master's degree": [
        "Data Scientist", "Product Manager", "Strategy Consultant",
        "Operations Manager", "UX Designer", "Marketing Manager",
        "Business Analyst", "Financial Analyst", "University Professor",
        "Clinical Psychologist", "Healthcare Administrator", "MBA-level roles",
        "Research Scientist", "Policy Analyst", "Urban Planner",
    ],
    "Doctorate": [
        "University Professor", "Research Scientist", "Physician",
        "Clinical Psychologist", "Data Scientist", "AI/ML Engineer",
        "Research Director", "Chief Scientist", "Medical Specialist",
        "Biotech Researcher", "Policy Expert", "Think Tank Fellow",
    ],
}

# Income brackets aligned with occupation seniority
INCOME_OCCUPATION_MAP = {
    "< $25k": [
        "Retail Associate", "Customer Service Rep", "Entry-level positions",
        "Freelance Designer (starting)", "Part-time roles",
    ],
    "$25k-$50k": [
        "Teacher", "Social Worker", "Customer Service Manager",
        "Retail Manager", "Restaurant Manager", "Electrician", "Plumber",
        "Entry-level Software Engineer", "Junior Analyst",
    ],
    "$50k-$75k": [
        "Software Engineer", "Teacher", "Accountant", "Marketing Specialist",
        "Data Analyst", "Project Manager", "Financial Analyst",
        "Registered Nurse", "Physical Therapist", "Real Estate Agent",
    ],
    "$75k-$100k": [
        "Senior Software Engineer", "Product Manager", "UX Designer",
        "Marketing Manager", "Data Scientist", "Business Analyst",
        "Financial Advisor", "Operations Manager", "Clinical Psychologist",
    ],
    "$100k-$150k": [
        "Senior Product Manager", "Engineering Manager", "Data Scientist",
        "Strategy Consultant", "Marketing Director", "Physician (early career)",
        "Investment Banker (analyst)", "Tech Lead", "Solutions Architect",
    ],
    "> $150k": [
        "Senior Engineering Manager", "Director of Product", "VP roles",
        "Physician", "Investment Banker", "Strategy Consultant (senior)",
        "Entrepreneur (successful)", "C-level Executive", "Principal Engineer",
        "Senior Data Scientist", "Chief Architect",
    ],
}


def get_consistent_occupation(
    education_level: Optional[str],
    income_bracket: Optional[str],
    age: int,
    fallback_occupations: list
) -> str:
    """
    Get an occupation that's consistent with education, income, and age.

    Args:
        education_level: Education level of the persona
        income_bracket: Income bracket of the persona
        age: Age of the persona
        fallback_occupations: Default occupation list as fallback

    Returns:
        A consistent occupation string
    """
    potential_occupations = set(fallback_occupations)

    # Filter by education level
    if education_level and education_level in EDUCATION_OCCUPATION_MAP:
        education_matches = set(EDUCATION_OCCUPATION_MAP[education_level])
        potential_occupations &= education_matches

    # Filter by income bracket
    if income_bracket and income_bracket in INCOME_OCCUPATION_MAP:
        income_matches = set(INCOME_OCCUPATION_MAP[income_bracket])
        # Only filter if there's overlap, otherwise use education filter
        overlap = potential_occupations & income_matches
        if overlap:
            potential_occupations = overlap

    # Age-based adjustments
    if age < 25:
        # Recent graduates - prefer entry-level
        junior_keywords = ['Junior', 'Entry', 'Associate', 'Analyst', 'Coordinator']
        junior_occupations = [
            occ for occ in potential_occupations
            if any(keyword in occ for keyword in junior_keywords)
        ]
        if junior_occupations:
            potential_occupations = set(junior_occupations)

    elif age >= 50:
        # Senior professionals - prefer leadership roles
        senior_keywords = ['Senior', 'Director', 'Manager', 'Lead', 'Chief', 'Principal', 'VP']
        senior_occupations = [
            occ for occ in potential_occupations
            if any(keyword in occ for keyword in senior_keywords)
        ]
        if senior_occupations:
            potential_occupations = set(senior_occupations)

    # Return random from filtered set, or fallback
    if potential_occupations:
        return random.choice(list(potential_occupations))

    # If no match found, return occupation appropriate for education
    if education_level and education_level in EDUCATION_OCCUPATION_MAP:
        return random.choice(EDUCATION_OCCUPATION_MAP[education_level])

    return random.choice(fallback_occupations)


def validate_occupation_consistency(
    occupation: str,
    education_level: Optional[str],
    income_bracket: Optional[str],
    age: int
) -> Dict[str, bool]:
    """
    Validate if occupation is consistent with demographic attributes.

    Returns:
        Dictionary with consistency checks
    """
    checks = {
        "education_consistent": True,
        "income_consistent": True,
        "age_appropriate": True,
    }

    # Check education consistency
    if education_level and education_level in EDUCATION_OCCUPATION_MAP:
        expected_occupations = EDUCATION_OCCUPATION_MAP[education_level]
        # Check if occupation matches or is similar
        checks["education_consistent"] = any(
            occ.lower() in occupation.lower() or occupation.lower() in occ.lower()
            for occ in expected_occupations
        )

    # Check income consistency
    if income_bracket and income_bracket in INCOME_OCCUPATION_MAP:
        expected_occupations = INCOME_OCCUPATION_MAP[income_bracket]
        checks["income_consistent"] = any(
            occ.lower() in occupation.lower() or occupation.lower() in occ.lower()
            for occ in expected_occupations
        )

    # Check age appropriateness
    if age < 25 and any(word in occupation for word in ['Senior', 'Director', 'VP', 'Chief']):
        checks["age_appropriate"] = False

    if age >= 55 and any(word in occupation for word in ['Junior', 'Entry', 'Intern']):
        checks["age_appropriate"] = False

    return checks
