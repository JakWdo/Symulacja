#!/usr/bin/env python3
"""
AI Learning Assistant - Główna komenda

Usage:
    /learn                         # Pokaż welcome screen + dziedziny
    /learn "quantum computing"     # Rozpocznij kurs AI-generowany
    /learn --domain backend        # Zmień aktywną dziedzinę
    /learn --domains               # Pokaż wszystkie dziedziny
    /learn continue                # Kontynuuj ostatni kurs
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_config, save_config
from domain_manager import (
    get_active_domain, set_active_domain, list_domains, get_domain
)
from course_planner import (
    extract_concepts_from_goal, create_course_plan, format_course_preview
)
from course_manager import create_course, list_active_courses, load_course_library, start_library_course


def show_welcome():
    """
    Wyświetl welcome screen z krótkim przeglądem dziedzin
    """
    print("# 🎓 Learn-by-Doing - AI Learning Assistant")
    print()

    # Active domain
    active = get_active_domain()
    if active:
        domain_id = active.get('id', '')
        domain_name = active.get('name', '')
        domain_icon = active.get('icon', '📚')
        concepts_count = active.get('concepts_count', 0)
        mastered_count = active.get('mastered_count', 0)
        progress_pct = (mastered_count / concepts_count * 100) if concepts_count > 0 else 0

        print(f"## {domain_icon} Aktywna Dziedzina: **{domain_name}**")
        print(f"Progress: {mastered_count}/{concepts_count} konceptów ({progress_pct:.0f}%)")
        print()

    # Dostępne dziedziny
    print("## 📚 Dostępne Dziedziny:")
    print()

    domains = list_domains()
    for domain in domains:
        icon = domain.get('icon', '📚')
        name = domain.get('name', '')
        description = domain.get('description', '')
        is_active = active and domain.get('id') == active.get('id')
        marker = "➡️ " if is_active else "   "

        print(f"{marker}{icon} **{name}** - {description}")

    print()
    print("## 💡 Jak zacząć?")
    print()
    print("```")
    print('/learn "Redis caching w FastAPI"    # Rozpocznij kurs')
    print("/learn --domain ai_ml               # Zmień dziedzinę")
    print("/learn --domains                    # Pokaż szczegóły")
    print("```")
    print()


def list_domains_brief():
    """
    Pokaż wszystkie dziedziny z progress bars
    """
    print("# 📚 Wszystkie Dziedziny Nauki")
    print()

    domains = list_domains()

    for domain in domains:
        icon = domain.get('icon', '📚')
        name = domain.get('name', '')
        description = domain.get('description', '')
        concepts_count = domain.get('concepts_count', 0)
        mastered_count = domain.get('mastered_count', 0)

        print(f"## {icon} {name}")
        print(f"_{description}_")
        print()

        if concepts_count > 0:
            progress_pct = (mastered_count / concepts_count * 100)
            bar_length = 15
            filled = int((mastered_count / concepts_count) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"**Progress:** {bar} {progress_pct:.0f}% ({mastered_count}/{concepts_count})")
        else:
            print(f"**Progress:** ░░░░░░░░░░░░░░░ 0% (0/0)")

        print()

    print("**Zmień aktywną:** `/learn --domain <id>`")
    print()


def set_domain_active(domain_id: str):
    """
    Ustaw aktywną dziedzinę

    Args:
        domain_id: ID dziedziny (np. "backend", "ai_ml")
    """
    success = set_active_domain(domain_id)

    if success:
        domain = get_domain(domain_id)
        icon = domain.get('icon', '📚')
        name = domain.get('name', '')
        description = domain.get('description', '')

        print(f"# {icon} Aktywna Dziedzina: **{name}**")
        print()
        print(f"_{description}_")
        print()
        print("System będzie priorytetowo śledzić tę dziedzinę.")
        print()
        print(f"Użyj `/learn \"cel\"` aby rozpocząć kurs w dziedzinie **{name}**")
    else:
        print(f"❌ **Błąd:** Nie znaleziono dziedziny `{domain_id}`")
        print()
        print("Dostępne:")
        for domain in list_domains():
            print(f"  - `{domain['id']}` - {domain['name']}")


def start_course_planning(goal: str):
    """
    Rozpocznij planowanie kursu AI

    Args:
        goal: Cel nauki (np. "Redis caching w FastAPI")
    """
    print(f"# 📚 Planuję kurs: **{goal}**")
    print()

    # Get active domain
    active = get_active_domain()
    domain_id = "software-engineering"  # default
    if active:
        domain_icon = active.get('icon', '📚')
        domain_name = active.get('name', '')
        domain_id = active.get('id', 'software-engineering')
        print(f"{domain_icon} **Dziedzina:** {domain_name}")
        print()

    print("🤖 **Analizuję cel i tworzę plan kursu...**")
    print()

    # Extract concepts from goal
    concept_ids = extract_concepts_from_goal(goal, domain_id)

    if not concept_ids:
        print("❌ **Nie znalazłem konceptów pasujących do celu.**")
        print()
        print("💡 Spróbuj bardziej konkretnego celu, np:")
        print("   - 'FastAPI async patterns'")
        print("   - 'Redis caching w backend'")
        print("   - 'React hooks i state management'")
        print()
        return

    print(f"✅ Znalazłem {len(concept_ids)} konceptów do nauczenia")
    print()

    # Use default preferences (intermediate, standard, balanced)
    # W przyszłości można dodać interaktywny wybór przez Claude
    preferences = {
        "level": "intermediate",  # Zakładam średni poziom
        "time": "standard",       # ~8-10h kurs
        "style": "balanced"       # Mix teorii i praktyki
    }

    # Create course plan
    course_plan = create_course_plan(goal, preferences, domain_id)

    if not course_plan:
        print("❌ **Nie udało się stworzyć kursu**")
        print()
        return

    # Show preview
    preview = format_course_preview(course_plan)
    print(preview)

    # Save course to active_courses.json
    course_id = create_course(course_plan)

    print(f"✅ **Kurs zapisany!** ID: `{course_id}`")
    print()
    print("📖 **Rozpocznij naukę:**")
    print(f'   Powiedz "Zacznij Lekcję 1" lub użyj `/learn continue`')
    print()


def show_course_library():
    """
    Pokaż dostępne kursy z course library
    """
    print("# 📚 Course Library - Gotowe Kursy")
    print()
    print("**Predefiniowane kursy gotowe do użycia:**")
    print()

    courses = load_course_library()

    if not courses:
        print("❌ **Brak kursów w library**")
        print()
        return

    for i, course in enumerate(courses, 1):
        course_id = course.get('id', '')
        title = course.get('title', 'Unnamed')
        description = course.get('description', '')
        icon = course.get('icon', '📚')
        level = course.get('level', 'intermediate')
        time = course.get('estimated_hours', 0)
        lessons = course.get('total_lessons', 0)
        difficulty = course.get('difficulty', 3)
        tags = ', '.join(course.get('tags', []))

        # Difficulty indicator
        diff_emoji = "🟢" if difficulty <= 2 else "🟡" if difficulty <= 3 else "🔴"

        print(f"## {i}. {icon} {title}")
        print(f"**ID:** `{course_id}`")
        print(f"**Opis:** {description}")
        print(f"**Parametry:** {diff_emoji} {level} | ⏱️ ~{time:.1f}h | 📖 {lessons} lekcji")
        print(f"**Tags:** {tags}")
        print()
        print(f"**Rozpocznij:** `/learn --start {course_id}`")
        print()

    print("---")
    print()
    print("💡 **Jak używać:**")
    print("1. Wybierz kurs z listy")
    print("2. Użyj `/learn --start <course-id>` aby rozpocząć")
    print("3. Kontynuuj przez `/learn continue`")
    print()


def continue_last_course():
    """
    Kontynuuj ostatni aktywny kurs
    """
    print("# 📖 Kontynuuj Naukę")
    print()

    # Get active courses
    active_courses = list_active_courses()

    if not active_courses:
        print("❌ **Brak aktywnych kursów**")
        print()
        print("💡 Rozpocznij nowy kurs:")
        print('   `/learn "cel nauki"`')
        print()
        return

    # Get last active course (most recent)
    course = active_courses[-1]

    # Display course info
    title = course.get('title', 'Unnamed Course')
    current_lesson_num = course.get('current_lesson', 1)
    total_lessons = course.get('total_lessons', 0)
    completed_lessons = course.get('completed_lessons', 0)

    print(f"## 📚 {title}")
    print()
    print(f"**Progress:** {completed_lessons}/{total_lessons} lekcji ukończonych")
    print()

    # Get current lesson
    lessons = course.get('lessons', [])
    if not lessons:
        print("❌ **Brak lekcji w kursie**")
        return

    # Find current lesson (not completed)
    current_lesson = None
    for lesson in lessons:
        if not lesson.get('completed', False):
            current_lesson = lesson
            break

    if not current_lesson:
        print("✅ **Kurs ukończony!**")
        print()
        print(f"Gratulacje! Ukończyłeś wszystkie {total_lessons} lekcji.")
        print()
        return

    # Display current lesson
    lesson_num = current_lesson.get('num', 1)
    lesson_name = current_lesson.get('concept_name', 'Unknown')
    lesson_time = current_lesson.get('estimated_time_minutes', 60)

    print(f"## Lekcja {lesson_num}/{total_lessons}: {lesson_name}")
    print(f"⏱️ Szacowany czas: ~{lesson_time} min")
    print()

    # Show theory
    theory = current_lesson.get('theory', '')
    if theory:
        print(theory)
        print()

    # Show TODO(human)
    todo = current_lesson.get('todo_human', '')
    if todo:
        print(todo)
        print()

    print("---")
    print()
    print("💡 **Po ukończeniu powiedz:** 'done' lub 'ukończyłem lekcję'")
    print()


def main():
    """Główna funkcja"""
    args = sys.argv[1:]

    if not args:
        # /learn bez argumentów = welcome screen
        show_welcome()
        return

    command = args[0].lower()

    # Commands
    if command == "--domains":
        list_domains_brief()

    elif command == "--domain":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj ID dziedziny")
            print()
            print("Usage: `/learn --domain <domain-id>`")
            print()
            print("Dostępne:")
            for domain in list_domains():
                print(f"  - `{domain['id']}`")
        else:
            set_domain_active(args[1])

    elif command == "--library":
        show_course_library()

    elif command == "--start":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj ID kursu z library")
            print()
            print("Usage: `/learn --start <course-id>`")
            print()
            print("Zobacz dostępne kursy: `/learn --library`")
        else:
            course_id = args[1]
            print(f"# 🚀 Rozpoczynam kurs z library...")
            print()

            new_course_id = start_library_course(course_id)

            if new_course_id:
                print(f"✅ **Kurs rozpoczęty!** ID: `{new_course_id}`")
                print()
                print("📖 **Kontynuuj naukę:**")
                print('   `/learn continue`')
                print()
            else:
                print(f"❌ **Błąd:** Nie znaleziono kursu `{course_id}` w library")
                print()
                print("Zobacz dostępne: `/learn --library`")
                print()

    elif command == "continue":
        continue_last_course()

    else:
        # Main: start new course
        goal = " ".join(args)
        start_course_planning(goal)


if __name__ == "__main__":
    main()
