"""Configure Details Node - Zbiera szczegóły konfiguracji"""

from __future__ import annotations
import logging
from config import prompts, models
from app.services.shared.clients import build_chat_model
from app.services.study_designer.state_schema import ConversationState, add_message, get_last_user_message
from app.services.study_designer.nodes.gather_goal import parse_llm_json_response

logger = logging.getLogger(__name__)


async def configure_details_node(state: ConversationState) -> ConversationState:
    """Configure Details node."""
    session_id = state["session_id"]
    user_message = get_last_user_message(state) or ""

    template = prompts.get("study_designer.configure_details")
    prompt_text = template.render(
        research_method=state.get("research_method", ""),
        study_goal=state.get("study_goal", ""),
        user_message=user_message,
    )

    try:
        model_config = models.get("study_designer", "question_generation")
        llm = build_chat_model(**model_config.params)
        response = await llm.ainvoke(prompt_text)
        llm_output = parse_llm_json_response(response.content)
    except Exception as e:
        logger.error(f"[Configure Details] LLM failed: {e}")
        add_message(state, "assistant", "Ile person chcesz wygenerować? (np. 18)")
        return state

    add_message(state, "assistant", llm_output.get("assistant_message", ""))

    if llm_output.get("config_complete") and llm_output.get("config"):
        config = llm_output["config"]
        state["num_personas"] = config.get("num_personas", 18)

        if state.get("research_method") == "focus_group":
            state["focus_group_config"] = config
        elif state.get("research_method") == "survey":
            state["survey_config"] = config

        state["current_stage"] = "generate_plan"
        logger.info(f"[Configure Details] Config complete, transitioning to generate_plan")

    return state
