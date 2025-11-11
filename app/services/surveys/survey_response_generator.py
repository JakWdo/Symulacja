"""
Serwis Generowania Odpowiedzi na Ankiety

UWAGA: To jest cienki wrapper dla zachowania kompatybilności wstecznej.
Główna logika została przeniesiona do:
- response_generator_core.py - logika generowania odpowiedzi
- response_formatter.py - formatowanie i analityka

Po zaktualizowaniu wszystkich importów w projekcie, ten plik może być usunięty.
"""

# Re-export z response_generator_core dla kompatybilności wstecznej
from .response_generator_core import SurveyResponseGenerator

__all__ = ["SurveyResponseGenerator"]
