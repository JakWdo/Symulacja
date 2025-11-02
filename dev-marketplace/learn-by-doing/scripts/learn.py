#!/usr/bin/env python3
"""
Status trybu nauczania - dynamiczny podgląd
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_dynamic_concepts

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"

def get_status_emoji(streak):
    """Pobierz emoji statusu"""
    if streak >= 7:
        return "🔥🔥🔥", "ON FIRE!"
    elif streak >= 3:
        return "🔥", "Na fali!"
    elif streak >= 1:
        return "⭐", "Dobry start!"
    else:
        return "💤", "Pora wracać!"

def main():
    progress = load_progress()
    dynamic = load_dynamic_concepts()

    print("# 🎓 Status Trybu Nauczania")
    print()

    if not progress:
        print("⚠️ **Plugin dopiero się inicjalizuje...**")
        print()
        print("Twój postęp będzie śledzony od tej sesji!")
        print()
    else:
        sessions = progress.get("sessions", 0)
        streak = progress.get("streak_days", 0)
        emoji, status_text = get_status_emoji(streak)

        current_focus = progress.get("current_focus", {})
        focus_category = current_focus.get("category", "N/A")

        print(f"## {emoji} **{status_text}**")
        print()
        print(f"- **Sesja:** #{sessions}")
        print(f"- **Passa:** {streak} dni pod rząd")
        print(f"- **Focus:** {focus_category}")

        # Show auto-discovered count
        discovered_count = len(dynamic)
        if discovered_count > 0:
            print(f"- **Auto-discovered:** ⭐ {discovered_count} nowych technologii")

        print()

    print("## 🎯 Co robi ten plugin?")
    print()
    print("1. **Obserwuje** Twoją pracę nad projektem Sight")
    print("2. **Wyjaśnia** dlaczego coś działa (nie tylko jak)")
    print("3. **Pozostawia TODO(human)** do samodzielnej implementacji")
    print("4. **Śledzi postęp** i przypomina o powtórkach")
    print()

    print("## 🛠️ Dostępne komendy:")
    print()
    print("- `/learn-by-doing:learn` - Ten ekran (status)")
    print("- `/learn-by-doing:progress` - Dashboard postępów")
    print("- `/learn-by-doing:review` - Przegląd nauki")
    print("- `/learn-by-doing:concepts` - Lista wszystkich konceptów")
    print("- `/learn-by-doing:track-concepts` - Skanuj nowe technologie")
    print()

    print("## 📚 Jak działa tryb nauczania?")
    print()
    print("Podczas pracy będę:")
    print("- 💡 Wyjaśniał **DLACZEGO** coś działa (nie tylko JAK)")
    print("- ✍️ Zostawiał **TODO(human)** do samodzielnej implementacji")
    print("- 🔗 Pokazywał **powiązania** między konceptami w Sight")
    print("- 🤔 Zadawał **pytania** do refleksji")
    print()

    print("---")
    print()
    print("**Status:** ✅ Aktywny")
    print()
    print("_Szczęśliwego kodowania! 🚀_")

if __name__ == "__main__":
    main()
