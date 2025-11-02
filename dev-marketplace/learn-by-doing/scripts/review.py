#!/usr/bin/env python3
"""
Przegląd nauki - analiza practice log
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

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

def filter_logs_by_time(logs, days=1):
    """Filtruj logi według czasu"""
    cutoff = datetime.now() - timedelta(days=days)

    filtered = []
    for log in logs:
        timestamp = datetime.fromisoformat(log.get("timestamp", ""))
        if timestamp >= cutoff:
            filtered.append(log)

    return filtered

def analyze_activity(logs):
    """Analizuj aktywność"""
    if not logs:
        return None

    actions = [log.get("action") for log in logs]
    contexts = [log.get("context", {}).get("type") for log in logs]

    action_counts = Counter(actions)
    context_counts = Counter(contexts)

    files = [log.get("context", {}).get("file") for log in logs if log.get("context", {}).get("file")]
    unique_files = len(set(files))

    return {
        "total_actions": len(logs),
        "action_counts": dict(action_counts),
        "context_counts": dict(context_counts),
        "unique_files": unique_files,
        "files": files
    }

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

def format_context(context):
    """Formatuj typ kontekstu"""
    context_names = {
        "service": "🔧 Service Layer",
        "api_endpoint": "🌐 API Endpoint",
        "test": "🧪 Test",
        "other": "📄 Inny plik"
    }
    return context_names.get(context, f"❓ {context}")

def main():
    # Pobierz argument (today, week)
    period = sys.argv[1] if len(sys.argv) > 1 else "today"

    if period == "week":
        days = 7
        title = "Ostatnie 7 dni"
    else:
        days = 1
        title = "Dzisiaj"

    progress = load_progress()
    all_logs = load_practice_log()
    logs = filter_logs_by_time(all_logs, days)

    print(f"# 📝 Przegląd Nauki - {title}")
    print()

    if not logs:
        print("_Brak aktywności w tym okresie._")
        print()
        print("Zacznij pracować nad projektem, a Twoja aktywność zostanie tutaj zapisana!")
        return

    analysis = analyze_activity(logs)

    print(f"## 📊 Podsumowanie ({title.lower()})")
    print()
    print(f"- **Całkowita liczba akcji:** {analysis['total_actions']}")
    print(f"- **Edytowane pliki:** {analysis['unique_files']}")
    print()

    print("## 🎯 Akcje")
    print()
    for action, count in sorted(analysis['action_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"- {format_action(action)}: **{count}**")
    print()

    print("## 📁 Obszary pracy")
    print()
    if analysis['context_counts']:
        for context, count in sorted(analysis['context_counts'].items(), key=lambda x: x[1], reverse=True):
            print(f"- {format_context(context)}: **{count}** akcji")
    else:
        print("_Brak danych o kontekście_")
    print()

    print("## 📂 Najczęściej edytowane pliki")
    print()
    file_counts = Counter(analysis['files'])
    top_files = file_counts.most_common(5)

    if top_files:
        for file_name, count in top_files:
            print(f"- `{file_name}` - {count} edycji")
    else:
        print("_Brak danych o plikach_")

    print()
    print("---")
    print()

    if progress:
        streak = progress.get("streak_days", 0)
        if streak >= 3:
            print("🔥 **Świetna passa!** Trzymaj tempo!")
        else:
            print("💪 **Dobra robota!** Kontynuuj naukę!")

    print()
    print("_Użyj `/learn-by-doing:review week` aby zobaczyć ostatnie 7 dni_")

if __name__ == "__main__":
    main()
