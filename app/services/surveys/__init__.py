"""
Survey services.

Serwisy odpowiedzialne za generowanie odpowiedzi na ankiety:
- SurveyResponseGenerator - Generowanie odpowiedzi person na pytania ankietowe (główna klasa)
- SurveyResponseFormatter - Formatowanie i analityka odpowiedzi
"""

from .survey_response_generator import SurveyResponseGenerator
from .response_formatter import SurveyResponseFormatter

__all__ = [
    "SurveyResponseGenerator",
    "SurveyResponseFormatter",
]
