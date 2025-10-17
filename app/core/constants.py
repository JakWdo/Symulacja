"""
Utility constants dla systemu generowania person.

UWAGA: Ten plik zawiera TYLKO utility constants używane do:
- Normalizacji nazw miast (POLISH_LOCATIONS)
- Translacji EN→PL dla education/income (POLISH_EDUCATION_LEVELS, POLISH_INCOME_BRACKETS)

Demographics dla person są generowane przez:
1. Orchestration (Gemini 2.5 Pro) - tworzy briefe z demographics per segment
2. LLM (Gemini Flash) - generuje imiona, zawody, wartości bazując na briefach

NIE MA już statistical sampling z hardcoded constants!
"""

# ═══════════════════════════════════════════════════════════════════════════════
# POLSKIE STAŁE - UTILITY DLA NORMALIZACJI I TRANSLACJI
# ═══════════════════════════════════════════════════════════════════════════════

# Rozkład lokalizacji w Polsce - używany do normalizacji nazw miast
# (np. "warsaw" → "Warszawa", "krakow" → "Kraków")
POLISH_LOCATIONS = {
    "Warszawa": 0.20,
    "Kraków": 0.10,
    "Wrocław": 0.08,
    "Gdańsk": 0.06,
    "Poznań": 0.06,
    "Łódź": 0.05,
    "Katowice": 0.05,
    "Szczecin": 0.04,
    "Lublin": 0.04,
    "Białystok": 0.03,
    "Bydgoszcz": 0.03,
    "Gdynia": 0.02,
    "Częstochowa": 0.02,
    "Radom": 0.02,
    "Toruń": 0.02,
    "Inne miasta": 0.18,
}

# Polskie style komunikacji
POLISH_COMMUNICATION_STYLES = [
    "bezpośredni i szczery",
    "ciepły i serdeczny",
    "powściągliwy i formalny",
    "humorystyczny i sarkastyczny",
    "emocjonalny i ekspresyjny",
    "rzeczowy i konkretny",
    "grzeczny i uprzejmy",
    "krytyczny i wymagający",
    "opiekuńczy i wspierający",
    "stanowczy i asertywny",
]

# Polskie style podejmowania decyzji
POLISH_DECISION_STYLES = [
    "ostrożny i przemyślany",
    "kieruje się doświadczeniem",
    "konsultuje się z rodziną",
    "bazuje na tradycji",
    "praktyczny i pragmatyczny",
    "impulsywny ale intuicyjny",
    "analizuje wszystkie opcje",
    "kieruje się emocjami",
    "szuka bezpiecznych rozwiązań",
    "odważny gdy ma pewność",
]

# Polskie przedziały dochodowe (netto miesięcznie, na podstawie danych GUS 2024)
POLISH_INCOME_BRACKETS = {
    "< 5 000 zł": 0.15,      # Najniższe zarobki, minimalna krajowa ~2800 zł netto
    "5 000 - 8 000 zł": 0.25, # Poniżej średniej krajowej
    "7 000 - 10 000 zł": 0.25, # Wokół średniej krajowej (~6500 zł netto)
    "10 500 - 13 000 zł": 0.18, # Powyżej średniej
    "14 000 - 20 000 zł": 0.12, # Wyższe zarobki (specjaliści, menedżerowie)
    "> 25 000 zł": 0.05,     # Najwyższe zarobki (kadra zarządzająca, eksperci IT)
}

# Polskie poziomy wykształcenia (na podstawie danych GUS)
POLISH_EDUCATION_LEVELS = {
    "Podstawowe": 0.08,                    # Wykształcenie podstawowe
    "Gimnazjalne": 0.05,                   # Gimnazjum (stary system)
    "Zasadnicze zawodowe": 0.18,          # Szkoła zawodowa
    "Średnie ogólnokształcące": 0.15,     # Liceum ogólnokształcące
    "Średnie techniczne": 0.20,           # Technikum
    "Policealne": 0.04,                   # Szkoła policealna
    "Wyższe licencjackie": 0.12,          # Licencjat
    "Wyższe magisterskie": 0.18,          # Magisterium
}
