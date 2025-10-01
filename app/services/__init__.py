"""Service exports - using LangChain implementations as default."""

# Use LangChain implementations (preferred)
from .persona_generator_langchain import (
    PersonaGeneratorLangChain as PersonaGenerator,
    DemographicDistribution,
)
from .memory_service_langchain import MemoryServiceLangChain as MemoryService
from .focus_group_service_langchain import FocusGroupServiceLangChain as FocusGroupService
from .polarization_service import PolarizationService
from .adversarial_service import AdversarialService

__all__ = [
    "PersonaGenerator",
    "DemographicDistribution",
    "MemoryService",
    "FocusGroupService",
    "PolarizationService",
    "AdversarialService",
]
