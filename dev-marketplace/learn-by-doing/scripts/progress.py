#!/usr/bin/env python3
"""
Dynamiczny dashboard postępów - pokazuje rzeczywiste statystyki
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

def load_practice_log():
    """Wczytaj log praktyki"""
    log_file = DATA_DIR / "practice_log.jsonl"

    if not log_file.exists():
        return []

    logs = []
    for line in log_file.read_text().strip().split('\n'):
        if line:
            logs.append(json.loads(line))

    return logs

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
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%Y-%m-%d %H:%M")

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

def render_progress_bar(value, max_value, width=20):
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

    if not progress:
        print("⚠️ Brak danych o postępach. Plugin dopiero się inicjalizuje!")
        return

    # Statystyki
    sessions = progress.get("sessions", 0)
    streak = progress.get("streak_days", 0)
    mastered = progress.get("mastered_concepts", 0)
    total = progress.get("total_concepts", 0)
    focus = progress.get("current_focus", "N/A")

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

    # Learning paths
    paths = progress.get("learning_paths", {})

    print("# 📊 Dashboard Postępów")
    print()
    print("## 🎯 Twoje Statystyki")
    print()
    print(f"- **Sesje programowania:** {sessions} 📅")
    print(f"- **Passa dni:** {streak_emoji} {streak} dni pod rząd")
    print(f"- **Obecny focus:** {focus}")
    print(f"- **Opanowane koncepty:** {mastered}/{total}")
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
    print("## 🎓 Ścieżki Nauki")
    print()

    if paths:
        for path_id, path_data in paths.items():
            name = path_data.get("name", path_id)
            progress_val = path_data.get("progress", 0.0)
            concepts = path_data.get("concepts", [])

            bar = render_progress_bar(progress_val, 1.0, 15)
            print(f"### {name}")
            print(f"{bar}")
            print(f"_Koncepty:_ {', '.join(concepts)}")
            print()
    else:
        print("_Brak zdefiniowanych ścieżek_")

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
    print("_Użyj `/learn` aby zobaczyć status trybu nauczania_")

if __name__ == "__main__":
    main()
