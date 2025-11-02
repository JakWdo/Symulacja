#!/usr/bin/env python3
"""
Status trybu nauczania - dynamiczny podgląd
"""
import json
from pathlib import Path
from datetime import datetime

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"

def load_progress():
    """Wczytaj postęp uczenia się"""
    progress_file = DATA_DIR / "learning_progress.json"

    if not progress_file.exists():
        return None

    return json.loads(progress_file.read_text())

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
        focus = progress.get("current_focus", "N/A")

        print(f"## {emoji} **{status_text}**")
        print()
        print(f"- **Sesja:** #{sessions}")
        print(f"- **Passa:** {streak} dni pod rząd")
        print(f"- **Focus:** {focus}")
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
