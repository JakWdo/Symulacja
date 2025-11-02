#!/usr/bin/env python3
"""
Dynamiczny dashboard postępów - Multi-domain view (Universal Learning System v2.0)

Funkcjonalność:
- Progress per domain
- Global statistics
- Recent activity
- Category breakdown
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_practice_log, load_knowledge_base, load_dynamic_concepts
from domain_manager import get_active_domain, list_domains

def count_actions_by_type(logs):
    """Policz akcje według typu"""
    counts = {}
    for log in logs:
        action = log.get("action", "unknown")
        counts[action] = counts.get(action, 0) + 1
    return counts

def format_action(action):
    """Formatuj nazwę akcji"""
    action_names = {
        "file_create": "📝 Utworzenie pliku",
        "file_edit": "✏️ Edycja pliku",
        "test_run": "🧪 Uruchomienie testów",
        "git_operation": "🔀 Operacja Git",
        "bash_command": "💻 Komenda Bash",
        "quiz_result": "🎯 Quiz",
        "learning_interaction": "💡 Interakcja uczenia",
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
    # Load data
    progress = load_progress()
    logs = load_practice_log()
    all_domains = list_domains()
    active_domain = get_active_domain()

    if not progress:
        print("⚠️ Brak danych o postępach. Plugin dopiero się inicjalizuje!")
        return

    # Global stats
    sessions = progress.get("sessions", 0)
    streak = progress.get("streak_days", 0)

    # Emoji dla passy
    if streak >= 7:
        streak_emoji = "🔥🔥🔥"
    elif streak >= 3:
        streak_emoji = "🔥"
    else:
        streak_emoji = "⭐"

    # Actions
    action_counts = count_actions_by_type(logs)
    total_actions = sum(action_counts.values())

    # Header
    print("# 📊 DASHBOARD POSTĘPÓW - Universal Learning System v2.0")
    print()

    # Active domain highlight
    if active_domain:
        print(f"## 🎯 Aktywna Dziedzina: **{active_domain.get('name')}**")
        domain_concepts = active_domain.get('concepts_count', 0)
        domain_mastered = active_domain.get('mastered_count', 0)
        domain_progress = (domain_mastered / domain_concepts * 100) if domain_concepts > 0 else 0

        print(f"**Progress:** {domain_mastered}/{domain_concepts} konceptów ({domain_progress:.0f}%)")
        if domain_concepts > 0:
            bar = render_progress_bar(domain_mastered, domain_concepts, 20)
            print(f"{bar}")
        print()

    # Global stats
    print("## 📈 Globalne Statystyki")
    print()
    print(f"- **Sesje:** {sessions} 📅")
    print(f"- **Passa:** {streak_emoji} {streak} dni pod rząd")
    print(f"- **Całkowita aktywność:** {total_actions} akcji")
    print()

    # Multi-domain progress
    if len(all_domains) > 0:
        print("## 🎓 Postęp w Dziedzinach")
        print()

        for domain in all_domains:
            domain_id = domain.get("id")
            domain_name = domain.get("name")
            concepts = domain.get("concepts_count", 0)
            mastered = domain.get("mastered_count", 0)
            is_active = (active_domain and domain_id == active_domain.get("id"))

            marker = "➡️ " if is_active else "   "
            print(f"{marker}**{domain_name}**")

            if concepts > 0:
                bar = render_progress_bar(mastered, concepts, 15)
                print(f"{marker}{bar} ({mastered}/{concepts})")
            else:
                print(f"{marker}░░░░░░░░░░░░░░░ 0% (0/0)")

            print()

    # Activity breakdown
    print("## 📊 Aktywność według typu")
    print()

    if action_counts:
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"- {format_action(action)}: {count}")
    else:
        print("_Brak zarejestrowanych akcji_")

    print()

    # Recent quizzes (if any)
    quiz_logs = [log for log in logs if log.get("type") == "quiz_result"]
    if quiz_logs:
        print("## 🎯 Ostatnie Quizy")
        print()

        for quiz_log in quiz_logs[-3:]:  # Last 3 quizzes
            quiz_data = quiz_log.get("quiz", {})
            domain = quiz_data.get("domain", "Unknown")
            score = quiz_data.get("score", 0.0)
            num_questions = quiz_data.get("num_questions", 0)

            score_pct = int(score * 100)
            timestamp = quiz_log.get("timestamp", "")

            emoji = "🏆" if score >= 0.8 else "✅" if score >= 0.6 else "📚"
            print(f"{emoji} **{domain}**: {score_pct}% ({int(score * num_questions)}/{num_questions}) - {timestamp[:10]}")

        print()

    # Footer
    print("---")
    print()
    print("**Dostępne komendy:**")
    print("- `/learn` - Zarządzaj dziedzinami")
    print("- `/quiz` - Sprawdź wiedzę")
    print("- `/review` - Przegląd nauki")
    print("- `/concepts` - Lista konceptów")
    print()


if __name__ == "__main__":
    main()
