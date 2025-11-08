"""Generate Plan Node - Generuje szczegółowy plan badania"""

from __future__ import annotations
import logging
from config import prompts, models
from app.services.shared.clients import build_chat_model
from app.services.study_designer.state_schema import ConversationState, add_message
from app.services.study_designer.nodes.gather_goal import parse_llm_json_response

logger = logging.getLogger(__name__)


async def generate_plan_node(state: ConversationState) -> ConversationState:
    """Generate Plan node - tworzy pełny plan badania."""
    session_id = state["session_id"]
    logger.info(f"[Generate Plan] Session {session_id}: Generating plan...")

    # Zbierz dane
    config = state.get("focus_group_config") or state.get("survey_config") or {}

    template = prompts.get("study_designer.generate_plan")
    prompt_text = template.render(
        study_goal=state.get("study_goal", ""),
        target_audience=str(state.get("target_audience", {})),
        research_method=state.get("research_method", ""),
        num_personas=state.get("num_personas", 18),
        config=str(config),
    )

    try:
        model_config = models.get("study_designer", "plan_generation")
        llm = build_chat_model(**model_config.params)

        logger.debug(f"[Generate Plan] Calling LLM for plan generation...")
        response = await llm.ainvoke(prompt_text)
        llm_output = parse_llm_json_response(response.content)

        plan_markdown = llm_output.get("plan_markdown", "")

        # Zapisz plan do state
        state["generated_plan"] = {
            "markdown_summary": plan_markdown,
            "estimated_time_seconds": llm_output.get("estimated_time_seconds", 300),
            "estimated_cost_usd": llm_output.get("estimated_cost_usd", 0.25),
            "estimated_tokens": llm_output.get("estimated_tokens", 150000),
        }

        # Dodaj plan jako wiadomość
        plan_message = f"✅ **Plan badania gotowy!**\n\n{plan_markdown}\n\n" \
                      f"**Czy zatwierdzasz ten plan?**\n" \
                      f"Odpowiedz: `zatwierdź` lub `modyfikuj [co zmienić]`"

        add_message(state, "assistant", plan_message)

        state["current_stage"] = "await_approval"
        logger.info(f"[Generate Plan] Plan generated, transitioning to await_approval")

    except Exception as e:
        logger.error(f"[Generate Plan] Failed: {e}")
        add_message(
            state,
            "assistant",
            "Przepraszam, nie udało się wygenerować planu. Spróbuj ponownie.",
        )

    return state
