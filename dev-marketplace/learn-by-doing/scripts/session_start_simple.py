#!/usr/bin/env python3
import json
import sys

output = {
    "hook_event_name": "SessionStart",
    "hookSpecificOutput": {
        "additionalContext": """
🎓 TRYB NAUCZANIA AKTYWNY - Projekt Sight

Będę Ci pomagał przez:
- 💡 Wyjaśnianie DLACZEGO coś działa (nie tylko JAK)
- ✍️ Zostawianie TODO(human) do samodzielnej implementacji
- 🔗 Pokazywanie powiązań między konceptami w Sight
- 🤔 Zadawanie pytań do refleksji

Dostępne komendy: /learn, /review, /progress

Szczęśliwego kodowania! 🚀
"""
    }
}

print(json.dumps(output))
sys.exit(0)
