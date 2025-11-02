#!/usr/bin/env python3
"""
Progress Dashboard - Minimal, domain-focused view

Funkcjonalność:
- Aktywna dziedzina z progress bar
- Przegląd wszystkich dziedzin
- Aktywne kursy (jeśli są)
- Krótki output (max 15 linii)
"""
import json
import sys
from pathlib import Path

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_config
from domain_manager import get_active_domain, list_domains


def render_progress_bar(value, max_value, width=15):
    """
    Renderuj progress bar

    Args:
        value: Aktualna wartość
        max_value: Maksymalna wartość
        width: Szerokość bara

    Returns:
        String z progress barem i procentem
    """
    if max_value == 0:
        filled = 0
        percentage = 0
    else:
        filled = int((value / max_value) * width)
        percentage = int((value / max_value) * 100)

    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage}%"


def load_active_courses():
    """
    Załaduj aktywne kursy z active_courses.json

    Returns:
        Lista kursów lub pusta lista jeśli plik nie istnieje
    """
    try:
        plugin_root = Path(__file__).parent.parent
        courses_file = plugin_root / "data" / "active_courses.json"

        if not courses_file.exists():
            return []

        with open(courses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('courses', [])
    except Exception:
        return []


def main():
    """Główna funkcja dashboardu"""
    # Load data
    active_domain = get_active_domain()
    all_domains = list_domains()
    active_courses = load_active_courses()

    # Header
    print("# 📊 Progress Dashboard")
    print()

    # Active domain (if set)
    if active_domain:
        domain_icon = active_domain.get('icon', '📚')
        domain_name = active_domain.get('name', '')
        concepts_count = active_domain.get('concepts_count', 0)
        mastered_count = active_domain.get('mastered_count', 0)

        print(f"## {domain_icon} Aktywna Dziedzina: **{domain_name}**")

        if concepts_count > 0:
            bar = render_progress_bar(mastered_count, concepts_count, 20)
            print(f"{bar} ({mastered_count}/{concepts_count})")
        else:
            print("░░░░░░░░░░░░░░░░░░░░ 0% (0/0)")

        print()

    # Domains overview
    if len(all_domains) > 0:
        print("## 🎓 Wszystkie Dziedziny")
        print()

        for domain in all_domains:
            domain_id = domain.get('id', '')
            domain_icon = domain.get('icon', '📚')
            domain_name = domain.get('name', '')
            concepts = domain.get('concepts_count', 0)
            mastered = domain.get('mastered_count', 0)
            is_active = (active_domain and domain_id == active_domain.get('id'))

            marker = "➡️ " if is_active else "   "
            bar = render_progress_bar(mastered, concepts, 15)

            print(f"{marker}{domain_icon} {domain_name}: {bar} ({mastered}/{concepts})")

        print()

    # Active courses (if any)
    if active_courses:
        print("## 📚 Aktywne Kursy")
        print()

        for course in active_courses[:3]:  # Max 3
            title = course.get('title', 'Untitled')
            progress = course.get('progress', 0)
            current_lesson = course.get('current_lesson', 1)
            total_lessons = len(course.get('lessons', []))

            print(f"- **{title}** (Lekcja {current_lesson}/{total_lessons}, {progress:.0f}%)")

        print()

    # Footer
    print("---")
    print()
    print("💡 **Dostępne komendy:**")
    print("- `/learn <cel>` - Rozpocznij nowy kurs")
    print("- `/learn --domain <id>` - Zmień dziedzinę")
    print("- `/quiz` - Sprawdź wiedzę")
    print()


if __name__ == "__main__":
    main()
