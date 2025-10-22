"""
Scentralizowane prompty LLM dla Market Research SaaS

Ten moduł zawiera wszystkie prompty używane przez serwisy AI/LLM.
Każdy prompt jest zdefiniowany jako:
- ChatPromptTemplate (dla LangChain)
- Funkcja generująca dynamiczny prompt (dla f-strings)
- Stałe stringowe (dla prostych promptów)

Struktura:
- personas.py - Prompty dla generacji person, needs, messaging
- focus_groups.py - Prompty dla dyskusji focus group i ankiet
- rag.py - Prompty dla Graph RAG i Cypher queries
"""

from app.core.prompts.personas import (
    PERSONA_GENERATION_SYSTEM_PROMPT,
    PERSONA_GENERATION_CHAT_PROMPT,
)

from app.core.prompts.focus_groups import (
    DISCUSSION_SUMMARIZER_SYSTEM_PROMPT,
    DISCUSSION_SUMMARIZER_CHAT_PROMPT,
    create_summary_prompt,
    create_focus_group_response_prompt,
    SURVEY_SINGLE_CHOICE_PROMPT,
    SURVEY_MULTIPLE_CHOICE_PROMPT,
    SURVEY_RATING_SCALE_PROMPT,
    SURVEY_OPEN_TEXT_PROMPT,
)

from app.core.prompts.rag import (
    CYPHER_GENERATION_SYSTEM_PROMPT,
    CYPHER_GENERATION_CHAT_PROMPT,
    GRAPH_RAG_ANSWER_SYSTEM_PROMPT,
    GRAPH_RAG_ANSWER_CHAT_PROMPT,
    get_graph_transformer_config,
)

__all__ = [
    # Personas (tylko stałe - funkcje przeniesione do serwisów)
    "PERSONA_GENERATION_SYSTEM_PROMPT",
    "PERSONA_GENERATION_CHAT_PROMPT",
    # Focus Groups
    "DISCUSSION_SUMMARIZER_SYSTEM_PROMPT",
    "DISCUSSION_SUMMARIZER_CHAT_PROMPT",
    "create_summary_prompt",
    "create_focus_group_response_prompt",
    "SURVEY_SINGLE_CHOICE_PROMPT",
    "SURVEY_MULTIPLE_CHOICE_PROMPT",
    "SURVEY_RATING_SCALE_PROMPT",
    "SURVEY_OPEN_TEXT_PROMPT",
    # RAG
    "CYPHER_GENERATION_SYSTEM_PROMPT",
    "CYPHER_GENERATION_CHAT_PROMPT",
    "GRAPH_RAG_ANSWER_SYSTEM_PROMPT",
    "GRAPH_RAG_ANSWER_CHAT_PROMPT",
    "get_graph_transformer_config",
]
