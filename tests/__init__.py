"""
Pakiet testów - Sight

Ten katalog zawiera kompleksowy zestaw testów dla aplikacji:
- Testy jednostkowe (unit tests) - działają bez środowiska
- Testy integracyjne - wymagają bazy danych
- Testy E2E - wymagają pełnego środowiska

Aby uruchomić wszystkie testy, zobacz JAK_TESTOWAĆ.md
"""

# Wersja test suite
__version__ = "2.0.0"

# Test categories
UNIT_TESTS = [
    "test_critical_paths",
    "test_core_config_security",
    "test_persona_generator",
    "test_persona_validator_service",
    "test_memory_service_langchain",
    "test_discussion_summarizer_service",
    "test_analysis_api",
    "test_graph_analysis_api",
    "test_auth_api",
    "test_main_api",
    "test_api_integration",
]

INTEGRATION_TESTS = [
    "test_models",
]

SERVICE_TESTS = [
    "test_focus_group_service",
    "test_graph_service",
    "test_survey_response_generator",
]

E2E_TESTS = [
    "test_e2e_integration",
]
