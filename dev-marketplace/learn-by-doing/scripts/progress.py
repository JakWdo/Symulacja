#!/usr/bin/env python3
"""
Dynamiczny dashboard postępów - pokazuje rzeczywiste statystyki
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_practice_log, load_knowledge_base, load_dynamic_concepts
from concept_manager import ConceptManager

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"

def count_actions_by_type(logs):
    """Policz akcje według typu"""
    counts = {}
    for log in logs:
        action = log.get("action", "unknown")
        counts[action] = counts.get(action, 0) + 1

    return counts

def get_recent_activity(logs, limit=5):
    """Pobierz ostatnie aktywności"""
    recent = logs[-limit:] if len(logs) > limit else logs
    return list(reversed(recent))

def format_timestamp(iso_str):
    """Formatuj timestamp"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_str

def format_action(action):
    """Formatuj nazwę akcji"""
    action_names = {
        "file_create": "📝 Utworzenie pliku",
        "file_edit": "✏️ Edycja pliku",
        "test_run": "🧪 Uruchomienie testów",
        "git_operation": "🔀 Operacja Git",
        "bash_command": "💻 Komenda Bash"
    }
    return action_names.get(action, f"❓ {action}")

def render_progress_bar(value, max_value, width=15):
    """Renderuj progress bar"""
    if max_value == 0:
        filled = 0
    else:
        filled = int((value / max_value) * width)

    bar = "█" * filled + "░" * (width - filled)
    percentage = int((value / max_value) * 100) if max_value > 0 else 0

    return f"{bar} {percentage}%"

def main():
    progress = load_progress()
    logs = load_practice_log()
    kb = load_knowledge_base()
    dynamic = load_dynamic_concepts()

    manager = ConceptManager(kb, dynamic)
    all_concepts = manager.get_all_concepts()

    if not progress:
        print("⚠️ Brak danych o postępach. Plugin dopiero się inicjalizuje!")
        return

    # Statystyki
    sessions = progress.get("sessions", 0)
    streak = progress.get("streak_days", 0)

    # Count mastered concepts
    user_concepts = progress.get("concepts", {})
    mastered = sum(1 for c in user_concepts.values() if c.get("mastery_level", 0) >= 3)
    total = len(all_concepts)

    current_focus = progress.get("current_focus", {})
    focus_category = current_focus.get("category", "N/A")

    # Emoji dla passy
    if streak >= 7:
        streak_emoji = "🔥🔥🔥"
    elif streak >= 3:
        streak_emoji = "🔥"
    else:
        streak_emoji = "⭐"

    # Akcje
    action_counts = count_actions_by_type(logs)
    total_actions = sum(action_counts.values())

    # Category progress
    categories_progress = progress.get("categories_progress", {})

    print("# 📊 Dashboard Postępów")
    print()
    print("## 🎯 Twoje Statystyki")
    print()
    print(f"- **Sesje programowania:** {sessions} 📅")
    print(f"- **Passa dni:** {streak_emoji} {streak} dni pod rząd")
    print(f"- **Obecny focus:** {focus_category}")
    print(f"- **Opanowane koncepty:** {mastered}/{total}")

    # Auto-discovered count
    discovered_count = len(dynamic)
    if discovered_count > 0:
        print(f"- **Auto-discovered:** ⭐ {discovered_count} technologii")

    print()

    print("## 📈 Twoja Aktywność")
    print()
    print(f"**Całkowita liczba akcji:** {total_actions}")
    print()

    if action_counts:
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"- {format_action(action)}: {count}")
    else:
        print("_Brak zarejestrowanych akcji_")

    print()
    print("## 🎓 Postęp w Kategoriach")
    print()

    if categories_progress:
        # Sort categories by progress (descending)
        sorted_cats = sorted(
            categories_progress.items(),
            key=lambda x: x[1].get("progress", 0),
            reverse=True
        )

        for category, cat_data in sorted_cats:
            mastered_cat = cat_data.get("mastered", 0)
            total_cat = cat_data.get("total_concepts", 0)
            progress_val = cat_data.get("progress", 0.0)

            if total_cat > 0:
                bar = render_progress_bar(mastered_cat, total_cat, 15)
                print(f"### {category}")
                print(f"{bar} ({mastered_cat}/{total_cat} mastered)")
                print()
    else:
        print("_Brak danych o kategoriach_")
        print("_Uruchom `/track-concepts` aby zaktualizować_")

    print()
    print("## ⏱️ Ostatnia Aktywność")
    print()

    recent = get_recent_activity(logs, 5)
    if recent:
        for log in recent:
            timestamp = format_timestamp(log.get("timestamp", ""))
            action = format_action(log.get("action", "unknown"))
            context = log.get("context", {})
            file_name = context.get("file", "N/A")

            print(f"- **{timestamp}** - {action} → `{file_name}`")
    else:
        print("_Brak aktywności_")

    print()
    print("---")
    print()
    print("💪 **Trzymaj tempo!** Każda sesja to krok w stronę mistrzostwa.")
    print()
    print("_Użyj `/concepts` aby zobaczyć wszystkie koncepty_")


if __name__ == "__main__":
    main()
