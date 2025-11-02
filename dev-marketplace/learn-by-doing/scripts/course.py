#!/usr/bin/env python3
"""
Course Command - Interactive Course Learning

Komendy:
    /course start "cel"         # Rozpocznij nowy kurs
    /course list                # Lista aktywnych kursów
    /course continue <id>       # Kontynuuj kurs (następna lekcja)
    /course done <id>           # Oznacz lekcję jako ukończoną
    /course skip <id>           # Pomiń lekcję (nie zalecane)
    /course progress <id>       # Pokaż postęp w kursie
    /course remove <id>         # Usuń kurs

Universal Learning System v2.3
"""

import sys
from pathlib import Path

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from course_planner import ask_user_preferences, create_course_plan, format_course_preview
from course_manager import (
    create_course, list_active_courses, format_courses_list,
    get_course, remove_course, move_to_completed
)
from lesson_conductor import (
    conduct_lesson, mark_lesson_done, skip_lesson, show_course_progress
)


# ============================================================================
# COMMANDS
# ============================================================================

def start_course(goal: str):
    """
    Rozpoczyna nowy kurs - interactive flow

    Args:
        goal: Cel użytkownika (np. "Dodaj ML do projektu")
    """
    print(f"# 🎓 Nowy Kurs: \"{goal}\"")
    print()

    # Step 1: Ask preferences
    preferences = ask_user_preferences()

    # Step 2: Create course plan
    print("# ⚙️ Tworzę plan kursu...")
    print()

    course_plan = create_course_plan(goal, preferences)

    if not course_plan:
        print("❌ **Błąd:** Nie udało się stworzyć kursu")
        print()
        print("Możliwe przyczyny:")
        print("- Nie znaleziono konceptów pasujących do celu")
        print("- Cel jest zbyt ogólny (spróbuj być bardziej konkretny)")
        print()
        print("Przykłady dobrych celów:")
        print('- "Dodaj system cache\'owania Redis"')
        print('- "Zaimplementuj ML recommendations"')
        print('- "Stwórz React dashboard z charts"')
        return

    # Step 3: Show preview
    print(format_course_preview(course_plan))

    # Step 4: Ask for confirmation
    confirm = input("Rozpocząć kurs? (yes/no): ").strip().lower()

    if confirm not in ["yes", "y", "tak", "t"]:
        print("❌ Anulowano tworzenie kursu")
        return

    # Step 5: Create course
    course_id = create_course(course_plan)

    print()
    print(f"# ✅ Kurs Utworzony!")
    print()
    print(f"**ID:** `{course_id}`")
    print()

    # Step 6: Start first lesson
    print("---")
    print()
    print("# 🚀 Rozpoczynamy Lekcję 1!")
    print()

    print(conduct_lesson(course_id, lesson_num=1))


def list_courses_command():
    """Lista wszystkich aktywnych kursów"""
    courses = list_active_courses()
    print(format_courses_list(courses))


def continue_course(course_id: str):
    """
    Kontynuuj kurs (następna lekcja)

    Args:
        course_id: Course ID
    """
    course = get_course(course_id)
    if not course:
        print(f"❌ Nie znaleziono kursu: {course_id}")
        print()
        print("Użyj `/course list` aby zobaczyć aktywne kursy")
        return

    print(conduct_lesson(course_id))


def done_lesson(course_id: str):
    """
    Oznacz bieżącą lekcję jako ukończoną

    Args:
        course_id: Course ID
    """
    print(mark_lesson_done(course_id))


def skip_lesson_command(course_id: str):
    """
    Pomiń bieżącą lekcję (nie zalecane)

    Args:
        course_id: Course ID
    """
    print(skip_lesson(course_id))


def progress_command(course_id: str):
    """
    Pokaż postęp w kursie

    Args:
        course_id: Course ID
    """
    print(show_course_progress(course_id))


def remove_course_command(course_id: str):
    """
    Usuń kurs

    Args:
        course_id: Course ID
    """
    course = get_course(course_id)
    if not course:
        print(f"❌ Nie znaleziono kursu: {course_id}")
        return

    print(f"# ⚠️ Usuwanie Kursu")
    print()
    print(f"**Kurs:** {course['title']}")
    print(f"**Postęp:** {course['completed_lessons']}/{course['total_lessons']} lessons")
    print()

    if course['completed_lessons'] > 0:
        confirm = input("Czy na pewno chcesz usunąć kurs z postępem? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y", "tak", "t"]:
            print("❌ Anulowano usuwanie")
            return

    success = remove_course(course_id)

    if success:
        print(f"✅ Kurs **{course['title']}** został usunięty")
    else:
        print("❌ Błąd podczas usuwania kursu")


def show_help():
    """Pokaż pomoc dla /course"""
    print("""# 🎓 /course - Interactive Course Learning

## Komendy:

### Rozpocznij Nowy Kurs
```bash
/course start "Dodaj ML do projektu"
/course start "Zaimplementuj Redis caching"
```

Claude zapyta o:
- Poziom (beginner/intermediate/advanced)
- Czas (quick/standard/deep)
- Styl (theory-first/practice-first/balanced)

Potem stworzy spersonalizowany plan kursu!

### Lista Kursów
```bash
/course list
```

### Kontynuuj Kurs (następna lekcja)
```bash
/course continue <course-id>
```

### Oznacz Lekcję jako Ukończoną
```bash
/course done <course-id>
```

### Pomiń Lekcję (nie zalecane)
```bash
/course skip <course-id>
```

### Pokaż Postęp
```bash
/course progress <course-id>
```

### Usuń Kurs
```bash
/course remove <course-id>
```

---

## Przykładowy Flow:

```bash
# 1. Rozpocznij kurs
/course start "Dodaj system email notifications"

# Claude pyta o preferencje...
# Tworzy plan 5 lekcji...

# 2. Przejdź pierwszą lekcję
# Claude pokazuje teorię + TODO(human)

# Wykonujesz zadanie...

# 3. Oznacz jako done
/course done email-notifications

# 4. Kontynuuj
/course continue email-notifications

# ...repeat dla każdej lekcji...

# 5. Ukończ kurs!
# 🎉 Gratulacje!
```

---

**Happy Learning! 🚀**
""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    args = sys.argv[1:]

    if not args:
        show_help()
        return

    command = args[0].lower()

    # Commands
    if command == "start":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj cel kursu")
            print()
            print("Usage: `/course start \"cel\"`")
            print()
            print("Przykłady:")
            print('  /course start "Dodaj ML do projektu"')
            print('  /course start "Zaimplementuj Redis caching"')
            return

        goal = " ".join(args[1:])
        # Remove quotes if present
        goal = goal.strip('"').strip("'")
        start_course(goal)

    elif command == "list":
        list_courses_command()

    elif command == "continue":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj course-id")
            print()
            print("Usage: `/course continue <course-id>`")
            print()
            print("Użyj `/course list` aby zobaczyć dostępne kursy")
            return

        course_id = args[1]
        continue_course(course_id)

    elif command == "done":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj course-id")
            print()
            print("Usage: `/course done <course-id>`")
            return

        course_id = args[1]
        done_lesson(course_id)

    elif command == "skip":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj course-id")
            print()
            print("Usage: `/course skip <course-id>`")
            return

        course_id = args[1]
        skip_lesson_command(course_id)

    elif command == "progress":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj course-id")
            print()
            print("Usage: `/course progress <course-id>`")
            return

        course_id = args[1]
        progress_command(course_id)

    elif command == "remove":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj course-id")
            print()
            print("Usage: `/course remove <course-id>`")
            return

        course_id = args[1]
        remove_course_command(course_id)

    elif command in ["help", "--help", "-h"]:
        show_help()

    else:
        print(f"❌ Nieznana komenda: {command}")
        print()
        print("Użyj `/course help` aby zobaczyć dostępne komendy")


if __name__ == "__main__":
    main()
