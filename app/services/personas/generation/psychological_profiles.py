"""
Moduł do próbkowania profili psychologicznych dla person

Zawiera logikę do:
- Próbkowania cech Big Five (OCEAN) z rozkładów normalnych
- Próbkowania wymiarów kulturowych Hofstede
"""

import numpy as np
from typing import Dict


def sample_big_five_traits(
    rng: np.random.Generator,
    personality_skew: dict[str, float] = None
) -> Dict[str, float]:
    """
    Próbkuj cechy osobowości Big Five z rozkładów normalnych

    Model Big Five (OCEAN) mierzy pięć głównych wymiarów osobowości:
    - Openness (otwartość): ciekawość, kreatywność
    - Conscientiousness (sumienność): organizacja, dyscyplina
    - Extraversion (ekstrawersja): towarzyskość, energia
    - Agreeableness (ugodowość): empatia, współpraca
    - Neuroticism (neurotyzm): emocjonalność, podatność na stres

    Args:
        rng: NumPy random generator
        personality_skew: Opcjonalny słownik do przesunięcia rozkładów.
                          Klucze: 'openness', 'conscientiousness', etc.
                          Wartości: 0.0-1.0 (0=niskie, 0.5=zbalansowane, 1.0=wysokie)

    Returns:
        Słownik z wartościami cech w przedziale [0, 1]
    """
    skew = personality_skew or {}

    traits = {}
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        # Domyślnie: średnia = 0.5, odchylenie standardowe = 0.15
        mean = skew.get(trait, 0.5)
        # Upewnij się że średnia jest w przedziale [0, 1]
        mean = np.clip(mean, 0.0, 1.0)

        # Losuj z rozkładu normalnego i przytnij do [0, 1]
        value = np.clip(rng.normal(mean, 0.15), 0, 1)
        traits[trait] = value

    return traits


def sample_cultural_dimensions(rng: np.random.Generator) -> Dict[str, float]:
    """
    Próbkuj wymiary kulturowe Hofstede

    Model Hofstede opisuje różnice kulturowe w 6 wymiarach:
    - power_distance: akceptacja nierówności władzy
    - individualism: indywidualizm vs kolektywizm
    - masculinity: asertywność vs troska o innych
    - uncertainty_avoidance: unikanie niepewności
    - long_term_orientation: orientacja długo- vs krótkoterminowa
    - indulgence: pobłażliwość vs powściągliwość

    Args:
        rng: NumPy random generator

    Returns:
        Słownik z wartościami wymiarów w przedziale [0, 1]
    """
    return {
        "power_distance": np.clip(rng.normal(0.5, 0.2), 0, 1),
        "individualism": np.clip(rng.normal(0.5, 0.2), 0, 1),
        "masculinity": np.clip(rng.normal(0.5, 0.2), 0, 1),
        "uncertainty_avoidance": np.clip(rng.normal(0.5, 0.2), 0, 1),
        "long_term_orientation": np.clip(rng.normal(0.5, 0.2), 0, 1),
        "indulgence": np.clip(rng.normal(0.5, 0.2), 0, 1),
    }
