"""Await Approval Node - Czeka na zatwierdzenie planu przez użytkownika"""

from __future__ import annotations
import logging
from app.services.study_designer.state_schema import ConversationState, add_message, get_last_user_message

logger = logging.getLogger(__name__)


async def await_approval_node(state: ConversationState) -> ConversationState:
    """Await Approval node - przetwarza decyzję użytkownika o planie."""
    session_id = state["session_id"]
    user_message = (get_last_user_message(state) or "").lower()

    logger.info(f"[Await Approval] Session {session_id}: User response: {user_message[:50]}")

    # Detect approval keywords
    approve_keywords = ["zatwierdź", "zatwierd", "ok", "zgoda", "tak", "approve", "yes"]
    modify_keywords = ["modyfikuj", "zmień", "popraw", "modify", "change"]
    reject_keywords = ["anuluj", "rezygnuj", "nie", "cancel", "reject"]

    if any(kw in user_message for kw in approve_keywords):
        # Plan zatwierdzony
        state["plan_approved"] = True
        state["current_stage"] = "execute"

        add_message(
            state,
            "assistant",
            "🎉 **Plan zatwierdzony!**\n\n"
            "Uruchamiam badanie... To może potrwać kilka minut.\n"
            "Będziesz otrzymywać real-time updates o postępie."
        )

        logger.info(f"[Await Approval] Plan approved, transitioning to execute")

    elif any(kw in user_message for kw in modify_keywords):
        # Użytkownik chce modyfikować
        state["current_stage"] = "configure_details"

        add_message(
            state,
            "assistant",
            "Rozumiem, wracamy do konfiguracji. Co chcesz zmienić?"
        )

        logger.info(f"[Await Approval] Modification requested, back to configure_details")

    elif any(kw in user_message for kw in reject_keywords):
        # Anulowanie
        state["plan_approved"] = False

        add_message(
            state,
            "assistant",
            "Rozumiem, anuluję sesję. Czy chcesz rozpocząć nowe badanie?"
        )

        logger.info(f"[Await Approval] Plan rejected")

    else:
        # Niejasna odpowiedź
        add_message(
            state,
            "assistant",
            "Nie jestem pewien Twojej decyzji. Proszę odpowiedz:\n"
            "- `zatwierdź` - aby uruchomić badanie\n"
            "- `modyfikuj [co zmienić]` - aby wrócić do konfiguracji\n"
            "- `anuluj` - aby anulować"
        )

    return state
