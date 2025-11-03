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
from data_manager import load_config, load_progress
from domain_manager import get_active_domain, list_domains
from datetime import datetime, timedelta, timezone


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


def render_activity_heatmap(progress_data, days=30):
    """
    Renderuj heatmapę aktywności (ostatnie X dni)

    Args:
        progress_data: Dict z learning_progress
        days: Liczba dni do pokazania (default: 30)

    Returns:
        String z heatmapą (7 rows × weeks)
    """
    # Get concepts with practice history
    concepts = progress_data.get('concepts', {})

    # Build activity dict: date -> practice count
    activity = {}
    for concept in concepts.values():
        for entry in concept.get('practice_history', []):
            timestamp = entry.get('timestamp')
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                    activity[date] = activity.get(date, 0) + 1
                except:
                    pass

    # Generate heatmap for last N days
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days-1)

    # Symbol mapping: 0 = ░, 1-2 = ▒, 3+ = ▓
    heatmap_lines = []
    week_days = []

    for day_offset in range(days):
        date = start_date + timedelta(days=day_offset)
        count = activity.get(date, 0)

        if count == 0:
            symbol = "░"
        elif count <= 2:
            symbol = "▒"
        else:
            symbol = "▓"

        week_days.append(symbol)

        # New week (every 7 days) or last day
        if len(week_days) == 7 or day_offset == days - 1:
            heatmap_lines.append(''.join(week_days))
            week_days = []

    return '\n'.join(heatmap_lines)


def get_top_concepts(progress_data, limit=5):
    """
    Pobierz top practiced concepts

    Args:
        progress_data: Dict z learning_progress
        limit: Ile konceptów zwrócić (default: 5)

    Returns:
        Lista top concepts (sorted by practice_count desc)
    """
    concepts = progress_data.get('concepts', {})

    # Sort by practice_count
    sorted_concepts = sorted(
        concepts.items(),
        key=lambda x: x[1].get('practice_count', 0),
        reverse=True
    )

    return sorted_concepts[:limit]


def render_streak(progress_data):
    """
    Renderuj streak z emoji

    Args:
        progress_data: Dict z learning_progress

    Returns:
        String z streak (np. "🔥 7 day streak!")
    """
    streak = progress_data.get('streak_days', 0)

    if streak == 0:
        return "💤 Brak streak - rozpocznij naukę!"
    elif streak == 1:
        return "⭐ 1 dzień streak - kontynuuj!"
    elif streak < 7:
        return f"🔥 {streak} dni streak!"
    elif streak < 30:
        return f"🔥🔥 {streak} dni streak! Niesamowite!"
    else:
        return f"🔥🔥🔥 {streak} dni streak! LEGENDA!"


def main():
    """Główna funkcja dashboardu"""
    # Load data
    active_domain = get_active_domain()
    all_domains = list_domains()
    active_courses = load_active_courses()
    progress_data = load_progress()

    # Header
    print("# 📊 Progress Dashboard")
    print()

    # Streak
    streak_msg = render_streak(progress_data)
    print(f"**{streak_msg}**")
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
            current_lesson = course.get('current_lesson', 1)
            total_lessons = course.get('total_lessons', 0)
            completed = course.get('completed_lessons', 0)

            bar = render_progress_bar(completed, total_lessons, 10)
            print(f"- **{title}** ({bar}) - Lekcja {current_lesson}/{total_lessons}")

        print()

    # Top Concepts
    top_concepts = get_top_concepts(progress_data, limit=3)
    if top_concepts:
        print("## 🏆 Top Practiced Concepts")
        print()

        for i, (concept_id, concept_data) in enumerate(top_concepts, 1):
            name = concept_data.get('name', concept_id)
            count = concept_data.get('practice_count', 0)
            domain = concept_data.get('domain', 'unknown')
            mastered = "⭐ MASTERED" if concept_data.get('mastered', False) else ""

            print(f"{i}. **{name}** ({domain}) - {count}× practiced {mastered}")

        print()

    # Activity Heatmap
    heatmap = render_activity_heatmap(progress_data, days=28)  # 4 weeks
    if heatmap and heatmap.strip() != '░░░░░░░':  # Show only if there's activity
        print("## 📅 Activity Heatmap (Last 28 Days)")
        print()
        print("```")
        print(heatmap)
        print("```")
        print("_(░ = brak, ▒ = 1-2, ▓ = 3+ practiced concepts per dzień)_")
        print()

    # Footer
    print("---")
    print()
    print("💡 **Dostępne komendy:**")
    print("- `/learn <cel>` - Rozpocznij nowy kurs")
    print("- `/learn continue` - Kontynuuj ostatni kurs")
    print("- `/learn --domain <id>` - Zmień dziedzinę")
    print("- `/quiz` - Sprawdź wiedzę")
    print()


if __name__ == "__main__":
    main()
