"""Select Method Node - Wybór metody badawczej"""

from __future__ import annotations
import logging
from config import prompts, models
from app.services.shared.clients import build_chat_model
from app.services.study_designer.state_schema import ConversationState, add_message, get_last_user_message
from app.services.study_designer.nodes.gather_goal import parse_llm_json_response

logger = logging.getLogger(__name__)


async def select_method_node(state: ConversationState) -> ConversationState:
    """Select Method node - wybiera metodę badawczą."""
    session_id = state["session_id"]
    logger.info(f"[Select Method] Session {session_id}: Processing")

    user_message = get_last_user_message(state) or ""

    template = prompts.get("study_designer.select_method")
    prompt_text = template.render(
        study_goal=state.get("study_goal", ""),
        target_audience=str(state.get("target_audience", {})),
        user_message=user_message,
    )

    try:
        model_config = models.get("study_designer", "question_generation")
        llm = build_chat_model(**model_config.params)
        response = await llm.ainvoke(prompt_text)
        llm_output = parse_llm_json_response(response.content)
    except Exception as e:
        logger.error(f"[Select Method] LLM failed: {e}")
        add_message(state, "assistant", "Wybierz metodę: focus_group, survey, personas, mixed")
        return state

    add_message(state, "assistant", llm_output.get("assistant_message", ""))

    if llm_output.get("method_selected") and llm_output.get("method"):
        state["research_method"] = llm_output["method"]
        state["current_stage"] = "configure_details"
        logger.info(f"[Select Method] Method: {llm_output['method']}, transitioning to configure_details")

    return state
