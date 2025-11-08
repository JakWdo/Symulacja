"""
Welcome Node - Początkowy node konwersacji Study Designer

Generuje welcome message i rozpoczyna konwersację.
Nie wymaga LLM - używa statycznego templatu.

Flow:
1. Tworzy welcome message
2. Dodaje do state.messages
3. Ustawia current_stage na "gather_goal"
"""

from __future__ import annotations

import logging
from app.services.study_designer.state_schema import ConversationState, add_message

logger = logging.getLogger(__name__)


WELCOME_MESSAGE = """Witaj w **Interaktywnym Projektowaniu Badań**! 🎯

Jestem asystentem AI, który pom

oże Ci zaprojektować badanie krok po kroku. Zadając pytania i zbierając informacje, stworzę szczegółowy plan badania dopasowany do Twoich potrzeb.

**Jak to działa?**
1. Zadaję pytania aby zrozumieć Twój cel i wymagania
2. Pomagam wybrać najlepszą metodę badawczą
3. Generuję profesjonalny plan badania z estymacjami
4. Po Twoim zatwierdzeniu - automatycznie wykonuję badanie

Zacznijmy! 🚀

**Jaki jest główny cel Twojego badania?**

_Przykłady:_
- "Chcę zbadać czy nowa funkcja premium będzie atrakcyjna dla użytkowników 25-35 lat"
- "Potrzebuję zrozumieć potrzeby młodych rodziców dotyczące aplikacji parentingowych"
- "Chcę przetestować 3 koncepty produktu i wybrać najlepszą"
"""


async def welcome_node(state: ConversationState) -> ConversationState:
    """
    Welcome node - rozpoczyna konwersację.

    Args:
        state: Aktualny stan konwersacji (powinien być pusty)

    Returns:
        ConversationState: Zaktualizowany stan z welcome message

    Side effects:
        - Dodaje welcome message do state.messages
        - Ustawia current_stage na "gather_goal"
    """
    logger.info(f"[Welcome Node] Session {state['session_id']}: Starting conversation")

    # Dodaj welcome message
    add_message(state, "assistant", WELCOME_MESSAGE)

    # Przejdź do następnego stage
    state["current_stage"] = "gather_goal"

    logger.info(
        f"[Welcome Node] Session {state['session_id']}: Welcome message sent, "
        f"transitioning to gather_goal"
    )

    return state
