"""
Logika dystrybucji demograficznej dla generatora person.

UWAGA: Ten moduł jest backward compatibility wrapper.
Główna logika została przeniesiona do:
- distribution_calculator.py - calculation logic
- distribution_validators.py - validation helpers

Ten moduł zawiera narzędzia do:
- Normalizacji wag i rozkładów prawdopodobieństwa
- Losowania wartości z rozkładów ważonych
- Aplikacji demographic presets (gen_z, millennials, etc.)
- Walidacji i filtrowania age groups
- Budowania dystrybucji lokalizacji (miasta, focus areas)

Użycie:
    builder = DistributionBuilder()

    # Normalize weights
    normalized = builder.normalize_weights({"A": 2.0, "B": 3.0})
    # → {"A": 0.4, "B": 0.6}

    # Apply preset
    distribution = builder.apply_demographic_preset(dist, "millennials")
"""

# Import wszystkich funkcji z nowych modułów
from .distribution_calculator import DistributionBuilder
from .distribution_validators import (
    age_group_bounds,
    age_group_overlaps,
    extract_polish_cities_from_description,
    map_focus_area_to_industries,
)

# Re-export dla backward compatibility
__all__ = [
    "DistributionBuilder",
    "age_group_bounds",
    "age_group_overlaps",
    "extract_polish_cities_from_description",
    "map_focus_area_to_industries",
]
