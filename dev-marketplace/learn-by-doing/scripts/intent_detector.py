"""
Intent Detection dla Natural Language Interface

Wykrywa intencje użytkownika z naturalnego języka i ekstraktuje entities.
"""

import re
from typing import Dict, Any, Optional


# Wzorce dla każdej intencji (keywords + patterns)
INTENT_PATTERNS = {
    "add_domain": {
        "keywords": ["dodaj dziedzinę", "dodać dziedzinę", "nowa dziedzina", "stwórz dziedzinę", "utworzyć dziedzinę"],
        "patterns": [
            r"doda[jć] dziedzin[ęę]\s+([a-zA-Z0-9\s]+)",
            r"nowa dziedzina\s+([a-zA-Z0-9\s]+)",
            r"stw[oó]rz dziedzin[ęę]\s+([a-zA-Z0-9\s]+)",
        ],
        "entity_key": "domain_name",
    },
    "create_course": {
        "keywords": ["stwórz kurs", "utworzyć kurs", "kurs o", "chcę się nauczyć", "naucz mnie", "rozpocznij kurs"],
        "patterns": [
            r"stw[oó]rz kurs\s+o\s+(.+)",
            r"kurs\s+o\s+(.+)",
            r"chc[ęe] si[ęe] nauczy[ćt]\s+(.+)",
            r"naucz mnie\s+(.+)",
            r"rozpocznij kurs\s+(.+)",
        ],
        "entity_key": "goal",
    },
    "show_progress": {
        "keywords": [
            "pokaż postępy",
            "moje postępy",
            "jak idę",
            "jak mi idzie",
            "progress",
            "jak idą moje postępy",
            "dashboard",
            "statystyki",
        ],
        "patterns": [],
        "entity_key": None,
    },
    "generate_quiz": {
        "keywords": ["quiz", "sprawdź wiedzę", "test", "zrób quiz", "zrób mi quiz", "sprawdź moją wiedzę"],
        "patterns": [
            r"quiz\s+z\s+([a-zA-Z0-9_]+)",
            r"quiz\s+([a-zA-Z0-9_]+)",
            r"sprawd[źz] wiedz[ęe]\s+z\s+([a-zA-Z0-9_]+)",
        ],
        "entity_key": "domain",
    },
    "complete_lesson": {
        "keywords": ["done", "ukończone", "ukończyłem", "zrobione", "skończone", "koniec lekcji", "gotowe"],
        "patterns": [],
        "entity_key": None,
    },
    "continue_course": {
        "keywords": [
            "kontynuuj",
            "dalej",
            "następna lekcja",
            "kolejna lekcja",
            "wznów kurs",
            "kontynuuj kurs",
        ],
        "patterns": [],
        "entity_key": None,
    },
    "set_active_domain": {
        "keywords": ["zmień dziedzinę", "ustaw dziedzinę", "aktywna dziedzina", "przełącz dziedzinę"],
        "patterns": [
            r"zmie[nń] dziedzin[ęe] na\s+([a-zA-Z0-9_]+)",
            r"ustaw dziedzin[ęe]\s+([a-zA-Z0-9_]+)",
            r"aktywna dziedzina\s+([a-zA-Z0-9_]+)",
            r"prze[łl]\u0105cz na\s+([a-zA-Z0-9_]+)",
        ],
        "entity_key": "domain",
    },
    "show_library": {
        "keywords": [
            "pokaż kursy",
            "dostępne kursy",
            "library",
            "biblioteka kursów",
            "co masz",
            "jakie kursy",
            "lista kursów",
        ],
        "patterns": [],
        "entity_key": None,
    },
    "start_library_course": {
        "keywords": ["zacznij kurs", "rozpocznij kurs", "start"],
        "patterns": [
            r"zacznij kurs\s+([a-zA-Z0-9\-_]+)",
            r"rozpocznij kurs\s+([a-zA-Z0-9\-_]+)",
            r"start\s+([a-zA-Z0-9\-_]+)",
        ],
        "entity_key": "course_id",
    },
    "show_domains": {
        "keywords": ["pokaż dziedziny", "jakie dziedziny", "lista dziedzin", "wszystkie dziedziny", "domains"],
        "patterns": [],
        "entity_key": None,
    },
}


def detect_intent(message: str) -> Dict[str, Any]:
    """
    Wykrywa intencję użytkownika z naturalnego tekstu.

    Args:
        message: Wiadomość użytkownika (natural language)

    Returns:
        {
            "intent": str | None - nazwa intencji lub None
            "entities": dict - wyekstraktowane entities (np. {domain: "backend"})
            "confidence": float - pewność wykrycia (0.0-1.0)
            "matched_by": str - co wykryło (keyword | pattern | none)
        }
    """
    message_lower = message.lower().strip()

    # Próbuj wykryć każdą intencję
    for intent_name, config in INTENT_PATTERNS.items():
        # 1. Sprawdź keywords
        for keyword in config["keywords"]:
            if keyword.lower() in message_lower:
                entities = {}
                confidence = 0.8

                # Jeśli są patterns, próbuj wyekstraktować entities
                if config["patterns"] and config["entity_key"]:
                    for pattern in config["patterns"]:
                        match = re.search(pattern, message_lower, re.IGNORECASE)
                        if match:
                            entities[config["entity_key"]] = match.group(1).strip()
                            confidence = 0.95
                            break

                return {
                    "intent": intent_name,
                    "entities": entities,
                    "confidence": confidence,
                    "matched_by": "keyword",
                }

        # 2. Sprawdź patterns (jeśli nie było keyword match)
        if config["patterns"] and config["entity_key"]:
            for pattern in config["patterns"]:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    entities = {config["entity_key"]: match.group(1).strip()}
                    return {
                        "intent": intent_name,
                        "entities": entities,
                        "confidence": 0.9,
                        "matched_by": "pattern",
                    }

    # Brak wykrytej intencji
    return {
        "intent": None,
        "entities": {},
        "confidence": 0.0,
        "matched_by": "none",
    }


def extract_domain_from_message(message: str) -> Optional[str]:
    """
    Ekstraktuje nazwę dziedziny z wiadomości.

    Args:
        message: Wiadomość użytkownika

    Returns:
        Nazwa dziedziny lub None
    """
    # Znane dziedziny (lowercase)
    known_domains = [
        "backend", "frontend", "ai_ml", "ai/ml", "database",
        "devops", "testing", "system_design", "system design",
        "security", "cloud", "mobile", "product", "design"
    ]

    message_lower = message.lower()

    for domain in known_domains:
        if domain in message_lower:
            # Normalizuj (ai/ml → ai_ml, system design → system_design)
            if domain == "ai/ml":
                return "ai_ml"
            elif domain == "system design":
                return "system_design"
            else:
                return domain.replace(" ", "_")

    return None


def should_handle_intent(intent_result: Dict[str, Any], confidence_threshold: float = 0.7) -> bool:
    """
    Decyduje czy intencja powinna być obsłużona.

    Args:
        intent_result: Wynik z detect_intent()
        confidence_threshold: Minimalna pewność (default 0.7)

    Returns:
        True jeśli intencja powinna być obsłużona
    """
    return (
        intent_result["intent"] is not None
        and intent_result["confidence"] >= confidence_threshold
    )


# Przykłady testowe (uruchamiane przez pytest lub ręcznie)
if __name__ == "__main__":
    test_messages = [
        "Chcę dodać dziedzinę Security",
        "Stwórz kurs o Docker networking",
        "Jak idą moje postępy?",
        "Zrób quiz z backendu",
        "done",
        "kontynuuj kurs",
        "Zmień dziedzinę na frontend",
        "Pokaż dostępne kursy",
        "Zacznij kurs backend-onboarding",
        "Hello, how are you?",  # Brak intencji
    ]

    print("🧪 Testing Intent Detection\n")
    for msg in test_messages:
        result = detect_intent(msg)
        print(f"Message: '{msg}'")
        print(f"  Intent: {result['intent']}")
        print(f"  Entities: {result['entities']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Should handle: {should_handle_intent(result)}")
        print()
