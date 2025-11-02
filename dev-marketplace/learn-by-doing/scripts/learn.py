#!/usr/bin/env python3
"""
Zarządzanie trybem nauczania - włączanie, wyłączanie i status

Usage:
    python3 learn.py           # Show status
    python3 learn.py status    # Show status
    python3 learn.py on        # Enable plugin
    python3 learn.py off       # Disable plugin
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_dynamic_concepts, load_config, save_config

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


def show_status(enabled: bool):
    """Wyświetl status pluginu"""
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
        focus_category = current_focus.get("category", "None")

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
    print("- `/learn-by-doing:learn on` - Włącz tryb nauczania")
    print("- `/learn-by-doing:learn off` - Wyłącz tryb nauczania")
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
    status_emoji = "✅" if enabled else "❌"
    status_text = "Aktywny" if enabled else "Wyłączony"
    print(f"**Status:** {status_emoji} {status_text}")
    print()
    if enabled:
        print("_Szczęśliwego kodowania! 🚀_")
    else:
        print("_Użyj `/learn-by-doing:learn on` aby włączyć._")


def enable_plugin():
    """Włącz plugin"""
    config = load_config()
    config["enabled"] = True
    save_config(config)

    print("# ✅ Tryb Nauczania Włączony")
    print()
    print("Plugin **learn-by-doing** jest teraz aktywny!")
    print()
    print("## Co się zmieni?")
    print()
    print("- 🎓 Welcome message przy każdej sesji")
    print("- 📝 Automatyczne śledzenie praktyki (PostToolUse hook)")
    print("- 💡 Wyjaśnienia i TODO(human) od Claude")
    print("- 📊 Statystyki postępów")
    print()
    print("_Użyj `/learn-by-doing:learn` aby zobaczyć status._")


def disable_plugin():
    """Wyłącz plugin"""
    config = load_config()
    config["enabled"] = False
    save_config(config)

    print("# ❌ Tryb Nauczania Wyłączony")
    print()
    print("Plugin **learn-by-doing** został dezaktywowany.")
    print()
    print("## Co się zmieni?")
    print()
    print("- ❌ Brak welcome message przy starcie sesji")
    print("- ❌ Brak automatycznego śledzenia praktyki")
    print("- ✅ Twoje dane postępu są zachowane")
    print()
    print("_Użyj `/learn-by-doing:learn on` aby włączyć ponownie._")


def main():
    """Główna funkcja"""
    # Parse arguments
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "status"

    # Load current config
    config = load_config()
    enabled = config.get("enabled", True)

    if command in ["on", "włącz", "enable"]:
        enable_plugin()
    elif command in ["off", "wyłącz", "disable"]:
        disable_plugin()
    elif command in ["status", ""]:
        show_status(enabled)
    else:
        print(f"❌ Nieznana komenda: {command}")
        print()
        print("Dostępne komendy:")
        print("  python3 learn.py          # Status")
        print("  python3 learn.py on       # Włącz")
        print("  python3 learn.py off      # Wyłącz")


if __name__ == "__main__":
    main()
