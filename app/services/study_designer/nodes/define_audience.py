"""
Define Audience Node - Zbiera szczegóły grupy docelowej

Używa LLM do ekstrakcji demografii i charakterystyk.
Podobny pattern jak gather_goal node.
"""

from __future__ import annotations
import logging
from config import prompts, models
from app.services.shared.clients import build_chat_model
from app.services.study_designer.state_schema import (
    ConversationState,
    add_message,
    get_last_user_message,
)
from app.services.study_designer.nodes.gather_goal import (
    format_conversation_history,
    parse_llm_json_response,
)

logger = logging.getLogger(__name__)


async def define_audience_node(state: ConversationState) -> ConversationState:
    """Define Audience node - zbiera grupę docelową."""
    session_id = state["session_id"]
    logger.info(f"[Define Audience] Session {session_id}: Processing")

    user_message = get_last_user_message(state)
    if not user_message:
        add_message(state, "assistant", "Proszę opisać grupę docelową dla badania.")
        return state

    # Przygotuj context
    conversation_history = format_conversation_history(state["messages"])
    study_goal = state.get("study_goal", "Nie określono")

    # Załaduj prompt
    template = prompts.get("study_designer.define_audience")
    prompt_text = template.render(
        study_goal=study_goal,
        conversation_history=conversation_history,
        user_message=user_message,
    )

    # Wywołaj LLM
    try:
        model_config = models.get("study_designer", "question_generation")
        llm = build_chat_model(**model_config.params)
        response = await llm.ainvoke(prompt_text)
        llm_output = parse_llm_json_response(response.content)

        logger.info(
            f"[Define Audience] Session {session_id}: "
            f"audience_extracted={llm_output.get('audience_extracted')}"
        )

    except Exception as e:
        logger.error(f"[Define Audience] Session {session_id}: LLM failed: {e}")
        add_message(
            state,
            "assistant",
            "Przepraszam, wystąpił błąd. Czy mógłbyś ponownie opisać grupę docelową?",
        )
        return state

    # Dodaj assistant message
    assistant_message = llm_output.get("assistant_message", "")
    if assistant_message:
        add_message(state, "assistant", assistant_message)

    # Jeśli audience wyekstraktowana → zapisz i przejdź dalej
    if llm_output.get("audience_extracted") and llm_output.get("audience"):
        state["target_audience"] = llm_output["audience"]
        state["current_stage"] = "select_method"
        logger.info(f"[Define Audience] Session {session_id}: Transitioning to select_method")
    else:
        logger.info(f"[Define Audience] Session {session_id}: Staying in define_audience")

    return state
