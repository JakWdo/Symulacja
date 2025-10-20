"""
Survey services.

Serwisy odpowiedzialne za generowanie odpowiedzi na ankiety:
- SurveyResponseGenerator - Generowanie odpowiedzi person na pytania ankietowe
"""

from .survey_response_generator import SurveyResponseGenerator

__all__ = [
    "SurveyResponseGenerator",
]
