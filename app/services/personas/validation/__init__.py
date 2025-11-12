"""
Persona Validation Module

Moduły odpowiedzialne za walidację person i dystrybucji demograficznych:
- PersonaValidator - Główny walidator person
- DemographicsFormatter - Formatowanie danych demograficznych
- DistributionCalculator - Kalkulacje dystrybucji demograficznych
- StatisticalValidation - Walidacja statystyczna rozkładów
- PersonaAuditService - Audit log dla person
"""

from .persona_validator import PersonaValidator
from .demographics_formatter import DemographicsFormatter
from .distribution_builder import DistributionBuilder
from .distribution_validators import (
    age_group_bounds,
    age_group_overlaps,
)
from .statistical_validation import validate_distribution
from .persona_audit_service import PersonaAuditService

__all__ = [
    "PersonaValidator",
    "DemographicsFormatter",
    "DistributionBuilder",
    "age_group_bounds",
    "age_group_overlaps",
    "validate_distribution",
    "PersonaAuditService",
]
