"""US-based demographic distributions and defaults.

Rozkłady demograficzne bazowane na danych z USA, używane jako domyślne
wartości dla projektów które nie mają określonych własnych preferencji.
"""

# Domyślne rozkłady demograficzne
DEFAULT_AGE_GROUPS = {
    "18-24": 0.15,
    "25-34": 0.25,
    "35-44": 0.20,
    "45-54": 0.18,
    "55-64": 0.12,
    "65+": 0.10,
}

DEFAULT_GENDERS = {
    "male": 0.49,
    "female": 0.49,
    "non-binary": 0.02,
}

DEFAULT_LOCATIONS = {
    "New York, NY": 0.15,
    "Los Angeles, CA": 0.12,
    "Chicago, IL": 0.10,
    "Houston, TX": 0.08,
    "Phoenix, AZ": 0.06,
    "Philadelphia, PA": 0.06,
    "San Antonio, TX": 0.05,
    "San Diego, CA": 0.05,
    "Dallas, TX": 0.05,
    "San Jose, CA": 0.04,
    "Other": 0.24,
}

DEFAULT_EDUCATION_LEVELS = {
    "High school": 0.25,
    "Some college": 0.20,
    "Bachelor's degree": 0.30,
    "Master's degree": 0.15,
    "Doctorate": 0.05,
    "Other": 0.05,
}

DEFAULT_INCOME_BRACKETS = {
    "< $25k": 0.15,
    "$25k-$50k": 0.20,
    "$50k-$75k": 0.22,
    "$75k-$100k": 0.18,
    "$100k-$150k": 0.15,
    "> $150k": 0.10,
}
