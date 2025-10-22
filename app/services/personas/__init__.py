"""
Serwisy zarządzania personami

Ten moduł zawiera wszystkie serwisy związane z lifecycle person:
- Generacja person (generator.py)
- Orkiestracja segment-based (orchestration.py)
- Walidacja (validator.py)
- Porównania (comparison.py)
- Batch processing (batch_processor.py)
- Audit logging (audit.py)
"""

from app.services.personas.generator import PersonaGeneratorLangChain, DemographicDistribution
from app.services.personas.orchestration import PersonaOrchestrationService
from app.services.personas.validator import PersonaValidator
from app.services.personas.comparison import PersonaComparisonService
from app.services.personas.batch_processor import PersonaBatchProcessor
from app.services.personas.audit import PersonaAuditService

__all__ = [
    "PersonaGeneratorLangChain",
    "DemographicDistribution",
    "PersonaOrchestrationService",
    "PersonaValidator",
    "PersonaComparisonService",
    "PersonaBatchProcessor",
    "PersonaAuditService",
]
