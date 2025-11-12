"""
Conversation Extractor Node - Multi-step extraction w 1 wywołaniu LLM

Zastępuje 5 starych nodes (gather_goal, define_audience, select_method, configure_details, generate_plan)
jednym inteligentnym node który wyciąga WSZYSTKIE informacje naraz.

Flow:
1. Zbiera conversation history + latest user message
2. Wywołuje Gemini Pro z multi-step extraction prompt
3. Parsuje structured JSON response
4. Aktualizuje state z wyekstraktowanymi danymi
5. Decyduje: extraction_complete? → generate_plan : continue_conversation

LLM: Gemini 2.5 Pro (temp=0.3 dla consistent JSON output)
Prompt: config/prompts/study_designer/conversation_extractor.yaml

Advantages vs old architecture:
- 5-9 LLM calls → 1-2 calls (-80% latency)
- Gemini Pro = lepsze JSON structured output (mniej parsing failures)
- Prostsza logika (bez complex state machine z 5 nodes)
- Szybsze feedback dla usera (mniej roundtrips)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from config import prompts, models
from app.services.shared.clients import build_chat_model
from app.services.study_designer.state_schema import (
    ConversationState,
    add_message,
    get_last_user_message,
)
from app.services.study_designer.nodes.gather_goal import (
    format_conversation_history,
)

logger = logging.getLogger(__name__)


async def conversation_extractor_node(state: ConversationState) -> ConversationState:
    """
    Conversation Extractor - wyciąga wszystkie dane badawcze w 1 wywołaniu LLM.

    Ekstrahuje:
    - study_goal (cel badania)
    - target_audience (demografia + behavioral)
    - research_method (personas/focus_group/survey)
    - config (num_personas, topics, questions, etc.)

    Args:
        state: Aktualny stan konwersacji

    Returns:
        ConversationState: Zaktualizowany stan z wyekstraktowanymi danymi

    Side effects:
        - Wywołuje Gemini Pro (1 LLM call)
        - Dodaje assistant message (jeśli follow-up needed)
        - Aktualizuje state z extracted data
        - Transition: extraction_complete? → 'generate_plan' : 'conversation_extractor'
    """
    session_id = state["session_id"]

    logger.info(
        f"[Conversation Extractor] Session {session_id}: Multi-step extraction starting",
        extra={"session_id": session_id, "stage": "conversation_extractor"}
    )

    # 1. Pobierz user message + conversation history
    user_message = get_last_user_message(state)
    if not user_message:
        logger.error(f"[Conversation Extractor] Session {session_id}: No user message found!")
        add_message(
            state,
            "assistant",
            "Nie otrzymałem Twojej wiadomości. Opowiedz mi o swoim badaniu - co chcesz zbadać?",
        )
        return state

    conversation_history = format_conversation_history(state["messages"][:-1])  # Exclude last (current) message

    logger.debug(
        f"[Conversation Extractor] Session {session_id}: History length = {len(state['messages'])} messages"
    )

    # 2. Prepare prompt
    try:
        template = prompts.get("study_designer.conversation_extractor")
        rendered_messages = template.render(
            conversation_history=conversation_history,
            user_message=user_message
        )
    except Exception as e:
        logger.error(
            f"[Conversation Extractor] Session {session_id}: Prompt rendering failed: {e}",
            exc_info=True
        )
        # Fallback
        add_message(
            state,
            "assistant",
            "Przepraszam, wystąpił błąd. Spróbujmy jeszcze raz - jaki jest cel Twojego badania?",
        )
        return state

    # 3. LLM call (Gemini Pro)
    try:
        model_config = models.get("study_designer", "conversation_extraction")
        llm = build_chat_model(**model_config.params)

        logger.info(
            f"[Conversation Extractor] Session {session_id}: Calling Gemini Pro for extraction"
        )

        response = await llm.ainvoke(rendered_messages)
        response_text = response.content

        logger.debug(
            f"[Conversation Extractor] Session {session_id}: LLM response length = {len(response_text)} chars"
        )

    except Exception as e:
        logger.error(
            f"[Conversation Extractor] Session {session_id}: LLM call failed: {e}",
            exc_info=True,
            extra={"session_id": session_id, "error": str(e)}
        )
        # Fallback
        add_message(
            state,
            "assistant",
            "Przepraszam, mam problem z przetworzeniem Twojej odpowiedzi. Spróbujmy jeszcze raz - opowiedz mi więcej o swoim badaniu.",
        )
        return state

    # 4. Parse JSON response
    try:
        # Try direct JSON parse (Gemini Pro should return valid JSON)
        extraction_data = json.loads(response_text)
        logger.info(f"[Conversation Extractor] Session {session_id}: JSON parsed successfully")

    except json.JSONDecodeError:
        # Fallback: Try to extract JSON from markdown code block
        logger.warning(f"[Conversation Extractor] Session {session_id}: Direct JSON parse failed, trying markdown extraction")

        if "```json" in response_text:
            try:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
                extraction_data = json.loads(json_str)
                logger.info(f"[Conversation Extractor] Session {session_id}: JSON extracted from markdown")
            except Exception as e:
                logger.error(
                    f"[Conversation Extractor] Session {session_id}: Markdown extraction failed: {e}",
                    exc_info=True
                )
                # Final fallback
                add_message(
                    state,
                    "assistant",
                    "Przepraszam, mam problem ze zrozumieniem. Czy możesz opisać cel swojego badania w prostych słowach?",
                )
                return state
        else:
            logger.error(f"[Conversation Extractor] Session {session_id}: No JSON found in response")
            add_message(
                state,
                "assistant",
                "Przepraszam, wystąpił błąd w przetwarzaniu. Spróbujmy jeszcze raz - jaki jest cel Twojego badania?",
            )
            return state

    # 5. Update state with extracted data
    try:
        # Study goal
        if extraction_data.get("study_goal", {}).get("extracted"):
            state["study_goal"] = extraction_data["study_goal"]["goal_text"]
            logger.info(
                f"[Conversation Extractor] Session {session_id}: Study goal extracted: {state['study_goal'][:50]}..."
            )

        # Target audience
        if extraction_data.get("target_audience", {}).get("extracted"):
            state["target_audience"] = extraction_data["target_audience"]
            logger.info(
                f"[Conversation Extractor] Session {session_id}: Target audience extracted"
            )

        # Research method
        if extraction_data.get("research_method", {}).get("extracted"):
            method = extraction_data["research_method"]["method"]
            state["research_method"] = method
            logger.info(
                f"[Conversation Extractor] Session {session_id}: Research method: {method}"
            )

        # Config
        if extraction_data.get("config", {}).get("extracted"):
            config_details = extraction_data["config"]["details"]
            state["research_config"] = config_details
            logger.info(
                f"[Conversation Extractor] Session {session_id}: Config extracted: {list(config_details.keys())}"
            )

    except Exception as e:
        logger.error(
            f"[Conversation Extractor] Session {session_id}: State update failed: {e}",
            exc_info=True
        )
        # Continue anyway - partial extraction is better than nothing

    # 6. Decision: extraction_complete?
    extraction_complete = extraction_data.get("extraction_complete", False)

    if extraction_complete:
        # All data collected → proceed to plan generation
        logger.info(
            f"[Conversation Extractor] Session {session_id}: ✅ Extraction complete, transitioning to generate_plan",
            extra={
                "session_id": session_id,
                "study_goal": state.get("study_goal", "N/A")[:50],
                "research_method": state.get("research_method", "N/A")
            }
        )
        state["current_stage"] = "generate_plan"

    else:
        # Missing data → ask follow-up question
        follow_up_question = extraction_data.get("follow_up_question", "Czy możesz podać więcej szczegółów?")

        logger.info(
            f"[Conversation Extractor] Session {session_id}: ❌ Extraction incomplete, asking follow-up"
        )

        add_message(state, "assistant", follow_up_question)

        # Stay in conversation_extractor stage
        state["current_stage"] = "conversation_extractor"

    return state
