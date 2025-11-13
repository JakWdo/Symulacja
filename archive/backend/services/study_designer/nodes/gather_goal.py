"""
Gather Goal Node - Zbiera cel badania od użytkownika

Używa LLM (Gemini Flash) do:
1. Ekstrakcji celu badania z odpowiedzi użytkownika
2. Generowania follow-up questions jeśli cel jest niejasny

Flow:
1. Pobiera ostatnią wiadomość użytkownika
2. Wywołuje LLM z promptem gather_goal
3. Parsuje JSON response
4. Jeśli goal_extracted=true → zapisuje do state, przechodzi dalej
5. Jeśli goal_extracted=false → zadaje follow-up, zostaje w tym node

LLM: Gemini 2.5 Flash (temp=0.8 dla kreatywności pytań)
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

logger = logging.getLogger(__name__)

# Circuit breaker config
MAX_PARSE_RETRIES = 3  # Max liczba prób parsowania JSON
FALLBACK_GOAL = "Użytkownik chce przeprowadzić badanie"  # Generic fallback goal


async def gather_goal_node(state: ConversationState) -> ConversationState:
    """
    Gather Goal node - zbiera cel badania.

    Args:
        state: Aktualny stan konwersacji

    Returns:
        ConversationState: Zaktualizowany stan

    Side effects:
        - Wywołuje LLM
        - Dodaje assistant message
        - Aktualizuje state['study_goal'] jeśli cel wyekstraktowany
        - Pozostaje w 'gather_goal' stage lub przechodzi do 'define_audience'

    Circuit Breaker:
        - Jeśli parsing JSON failuje > MAX_PARSE_RETRIES, używa fallback i przechodzi dalej
        - Zapobiega infinite loop z niepoprawnym JSON od LLM
    """
    session_id = state["session_id"]

    # Pobierz retry count (inicjalizuj jeśli nie istnieje)
    parse_retry_count = state.get("gather_goal_parse_retries", 0)

    logger.info(
        f"[Gather Goal] Session {session_id}: Processing user message "
        f"(retry count: {parse_retry_count}/{MAX_PARSE_RETRIES})"
    )

    # Pobierz ostatnią wiadomość użytkownika
    user_message = get_last_user_message(state)
    if not user_message:
        logger.error(f"[Gather Goal] Session {session_id}: No user message found!")
        # Fallback - poproś o wiadomość
        add_message(
            state,
            "assistant",
            "Nie otrzymałem Twojej odpowiedzi. Proszę, powiedz mi jaki jest cel Twojego badania?",
        )
        return state

    # Przygotuj context dla LLM
    conversation_history = format_conversation_history(state["messages"])

    # Załaduj prompt
    try:
        template = prompts.get("study_designer.gather_goal")
    except Exception as e:
        logger.error(f"[Gather Goal] Failed to load prompt: {e}")
        raise

    # Renderuj prompt
    prompt_text = template.render(
        conversation_history=conversation_history,
        user_message=user_message,
    )

    # Wywołaj LLM
    try:
        model_config = models.get("study_designer", "question_generation")
        llm = build_chat_model(**model_config.params)

        logger.debug(f"[Gather Goal] Session {session_id}: Calling LLM...")
        response = await llm.ainvoke(prompt_text)

        # Parse JSON response
        llm_output = parse_llm_json_response(response.content)

        logger.info(
            f"[Gather Goal] Session {session_id}: LLM response - "
            f"goal_extracted={llm_output['goal_extracted']}, "
            f"confidence={llm_output.get('confidence', 'unknown')}"
        )

    except Exception as e:
        logger.error(
            f"[Gather Goal] Session {session_id}: LLM call failed: {e}",
            exc_info=True,
            extra={"alert": True},  # Alert w GCP Logs
        )

        # Increment retry counter
        parse_retry_count += 1
        state["gather_goal_parse_retries"] = parse_retry_count

        # Circuit breaker: Po MAX_RETRIES użyj fallback i przejdź dalej
        if parse_retry_count >= MAX_PARSE_RETRIES:
            logger.warning(
                f"[Gather Goal] Session {session_id}: Circuit breaker triggered! "
                f"Max retries ({MAX_PARSE_RETRIES}) exceeded. Using fallback goal.",
                extra={"alert": True},
            )

            # Użyj fallback goal i przejdź do następnego stage
            state["study_goal"] = FALLBACK_GOAL
            state["study_goal_confirmed"] = False  # Mark as unconfirmed
            state["current_stage"] = "define_audience"

            add_message(
                state,
                "assistant",
                "Rozumiem, że chcesz przeprowadzić badanie. Przejdźmy dalej - "
                "opowiedz mi o grupie docelowej dla tego badania.",
            )

            # Reset retry counter
            state["gather_goal_parse_retries"] = 0

            return state

        # Retry: Poproś ponownie
        add_message(
            state,
            "assistant",
            "Przepraszam, wystąpił błąd podczas analizy Twojej odpowiedzi. "
            "Czy mógłbyś ponownie opisać cel Twojego badania?",
        )
        return state

    # Success! Reset retry counter
    state["gather_goal_parse_retries"] = 0

    # Dodaj assistant message
    assistant_message = llm_output.get("assistant_message", "")
    if assistant_message:
        add_message(state, "assistant", assistant_message)

    # Jeśli cel wyekstraktowany → zapisz i przejdź dalej
    if llm_output.get("goal_extracted") and llm_output.get("goal"):
        state["study_goal"] = llm_output["goal"]
        state["study_goal_confirmed"] = True
        state["current_stage"] = "define_audience"

        logger.info(
            f"[Gather Goal] Session {session_id}: Goal extracted successfully, "
            f"transitioning to define_audience"
        )
    else:
        # Zostań w gather_goal stage (follow-up question already added)
        logger.info(
            f"[Gather Goal] Session {session_id}: Goal unclear, staying in gather_goal"
        )

    return state


def format_conversation_history(messages: list[dict[str, str]]) -> str:
    """
    Formatuje historię konwersacji do czytelnego tekstu.

    Args:
        messages: Lista wiadomości [{"role": "user", "content": "..."}]

    Returns:
        str: Sformatowana historia
    """
    if not messages:
        return "(Brak historii konwersacji)"

    formatted = []
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        formatted.append(f"{role}: {content}")

    return "\n\n".join(formatted)


def parse_llm_json_response(response_text: str) -> dict[str, Any]:
    """
    Parsuje JSON response z LLM.

    Próbuje:
    1. Direct JSON parse
    2. Ekstraktuj JSON z markdown code block (```json ... ```)
    3. Fallback do error dict

    Args:
        response_text: Raw response z LLM

    Returns:
        dict: Parsed JSON

    Raises:
        ValueError: Jeśli nie udało się sparsować JSON
    """
    # Try direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try extract from markdown code block
    if "```json" in response_text:
        try:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass

    # If still failed, try to find any JSON-like structure
    import re

    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Complete failure
    logger.error(f"[Parse JSON] Failed to parse LLM response: {response_text[:200]}...")
    raise ValueError("Failed to parse JSON from LLM response")
