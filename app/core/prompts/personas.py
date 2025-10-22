"""
Prompty dla generacji person (tylko stałe tekstowe)

Ten moduł zawiera TYLKO tekstowe szablony promptów dla:
- Generacji person (PersonaGeneratorLangChain)

WAŻNE: Funkcje pomocnicze zostały przeniesione do odpowiednich serwisów:
- create_persona_prompt() → app/services/personas/generator.py
- create_segment_persona_prompt() → app/services/personas/generator.py
- ORCHESTRATION_PROMPT_BUILDER() → app/services/personas/orchestration.py
- SEGMENT_NAME_PROMPT_BUILDER() → app/services/personas/orchestration.py
- SEGMENT_CONTEXT_PROMPT_BUILDER() → app/services/personas/orchestration.py

Funkcje PERSONA_NEEDS_PROMPT_BUILDER i PERSONA_MESSAGING_PROMPT_BUILDER były nieużywane i zostały usunięte.
"""

from langchain_core.prompts import ChatPromptTemplate


# ============================================================================
# PERSONA GENERATION - Podstawowe prompty dla generacji person
# ============================================================================

PERSONA_GENERATION_SYSTEM_PROMPT = (
    "Jesteś ekspertem od badań rynkowych tworzącym realistyczne syntetyczne persony "
    "dla polskiego rynku. Zawsze odpowiadaj poprawnym JSONem."
)

PERSONA_GENERATION_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", PERSONA_GENERATION_SYSTEM_PROMPT),
    ("user", "{prompt}")
])
