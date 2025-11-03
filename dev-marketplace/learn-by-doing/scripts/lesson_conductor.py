#!/usr/bin/env python3
"""
Lesson Conductor - Guided Learning Experience

Odpowiedzialności:
- Wyświetlanie lekcji (teoria + TODO(human))
- Prowadzenie użytkownika krok po kroku
- Oznaczanie lekcji jako ukończone
- Pokazywanie postępu w kursie

Universal Learning System v2.3
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from course_manager import get_course, get_next_lesson, update_lesson_progress, get_active_courses
from data_manager import add_practiced_concept

logger = logging.getLogger(__name__)


# ============================================================================
# LESSON CONDUCTING
# ============================================================================

def conduct_lesson(course_id: str, lesson_num: Optional[int] = None) -> str:
    """
    Prowadzi użytkownika przez lekcję

    Args:
        course_id: Course ID
        lesson_num: Numer lekcji (None = następna)

    Returns:
        Formatted lesson display
    """
    course = get_course(course_id)
    if not course:
        return f"❌ Nie znaleziono kursu: {course_id}"

    # Get lesson
    if lesson_num is None:
        lesson = get_next_lesson(course_id)
        if not lesson:
            return "🎉 Gratulacje! Ukończyłeś wszystkie lekcje!"
    else:
        lesson = None
        for l in course["lessons"]:
            if l["num"] == lesson_num:
                lesson = l
                break

        if not lesson:
            return f"❌ Nie znaleziono lekcji {lesson_num}"

    # Format lesson display
    return format_lesson_display(course, lesson)


def format_lesson_display(course: Dict[str, Any], lesson: Dict[str, Any]) -> str:
    """
    Formatuje wyświetlanie lekcji

    Args:
        course: Course dict
        lesson: Lesson dict

    Returns:
        Formatted string
    """
    lesson_num = lesson["num"]
    total_lessons = course["total_lessons"]
    concept_name = lesson["concept_name"]
    category = lesson["category"]
    theory = lesson.get("theory", "")
    todo = lesson.get("todo_human", "")
    time = lesson.get("estimated_time_minutes", 60)

    # Progress bar
    progress_pct = ((lesson_num - 1) / total_lessons) * 100
    progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))

    display = f"""# 📚 Kurs: {course['title']}

**Progress:** {progress_bar} {lesson_num}/{total_lessons} lessons

---

## Lekcja {lesson_num}: {concept_name}

**Kategoria:** {category}
**Czas:** ~{time} minut

---

{theory}

---

{todo}

---

**Gdy skończysz, użyj:**
`/course done {course['id']}` - Oznacz lekcję jako ukończoną i przejdź do następnej

**Lub:**
`/course skip {course['id']}` - Pomiń tę lekcję (nie zalecane!)

"""

    return display


def mark_lesson_done(course_id: str) -> str:
    """
    Oznacza bieżącą lekcję jako ukończoną

    Args:
        course_id: Course ID

    Returns:
        Success message + następna lekcja lub gratulacje
    """
    course = get_course(course_id)
    if not course:
        return f"❌ Nie znaleziono kursu: {course_id}"

    current_lesson_num = course.get("current_lesson", 1)

    # Mark as done
    success = update_lesson_progress(course_id, current_lesson_num, completed=True)

    if not success:
        return "❌ Błąd podczas oznaczania lekcji"

    # Reload course (updated)
    course = get_course(course_id)
    completed = course["completed_lessons"]
    total = course["total_lessons"]

    # Check if all done
    if completed >= total:
        return f"""# 🎉 GRATULACJE!

Ukończyłeś cały kurs: **{course['title']}**!

**Statystyki:**
- ✅ {total} lekcji ukończonych
- ⏱️ ~{course['estimated_hours']:.1f}h nauki
- 🎯 Poziom: {course['level']}

**Co dalej?**
- Użyj swojej nowej wiedzy w projekcie!
- Rozpocznij nowy kurs: `/course start "cel"`
- Sprawdź postęp: `/progress`

Świetna robota! 🚀
"""

    # Show next lesson
    next_lesson = get_next_lesson(course_id)
    if next_lesson:
        return f"""# ✅ Lekcja {current_lesson_num} Ukończona!

**Postęp:** {completed}/{total} lessons

---

**Następna lekcja ({next_lesson['num']}):** {next_lesson['concept_name']}

Gotowy kontynuować? Użyj:
`/course continue {course_id}`
"""

    return "✅ Lekcja ukończona!"


def mark_current_lesson_done() -> str:
    """
    Oznacza bieżącą lekcję jako ukończoną (znajduje ostatni aktywny kurs automatycznie)

    Returns:
        Success message + następna lekcja lub gratulacje
    """
    # Get last active course
    active_courses = get_active_courses()

    if not active_courses:
        return """❌ **Brak aktywnych kursów**

💡 Rozpocznij nowy kurs:
   `/learn "cel nauki"`
"""

    # Use last active course
    course = active_courses[-1]
    course_id = course['id']

    # Get current lesson for logging
    current_lesson_num = course.get("current_lesson", 1)
    current_lesson = None
    for lesson in course.get("lessons", []):
        if lesson["num"] == current_lesson_num:
            current_lesson = lesson
            break

    # Mark as done using existing function
    result = mark_lesson_done(course_id)

    # Log practiced concept to progress tracker
    if current_lesson:
        concept_id = current_lesson.get("concept_id")
        concept_name = current_lesson.get("concept_name", "Unknown")
        domain = current_lesson.get("category", "General")  # category is mapped from domain

        try:
            add_practiced_concept(
                concept_id=concept_id,
                concept_name=concept_name,
                domain=domain,
                practice_type="lesson_completed",
                metadata={
                    "course_id": course_id,
                    "lesson_num": current_lesson_num,
                    "course_title": course.get("title", "")
                }
            )
            logger.info(f"Logged practiced concept: {concept_id}")
        except Exception as e:
            logger.warning(f"Failed to log practiced concept: {e}")
            # Non-critical, continue

    return result


def skip_lesson(course_id: str) -> str:
    """
    Pomija bieżącą lekcję (NIE oznacza jako completed)

    Args:
        course_id: Course ID

    Returns:
        Message + następna lekcja
    """
    course = get_course(course_id)
    if not course:
        return f"❌ Nie znaleziono kursu: {course_id}"

    current_lesson_num = course.get("current_lesson", 1)

    # Just move to next (without marking as completed)
    next_num = current_lesson_num + 1
    if next_num > course["total_lessons"]:
        return "📭 To była ostatnia lekcja! Wróć i ukończ pominięte."

    # Find next lesson
    next_lesson = None
    for lesson in course["lessons"]:
        if lesson["num"] == next_num:
            next_lesson = lesson
            break

    if next_lesson:
        # Update current_lesson pointer (bez marking as completed)
        from course_manager import load_courses, save_courses
        courses_data = load_courses()

        for c in courses_data["active_courses"]:
            if c["id"] == course_id:
                c["current_lesson"] = next_num
                save_courses(courses_data)
                break

        return f"""# ⏭️ Pominięto Lekcję {current_lesson_num}

**Uwaga:** Lekcja NIE została oznaczona jako ukończona!

**Następna lekcja ({next_num}):** {next_lesson['concept_name']}

Użyj `/course continue {course_id}` aby kontynuować.
"""

    return "❌ Brak następnej lekcji"


def show_course_progress(course_id: str) -> str:
    """
    Pokazuje szczegółowy postęp w kursie

    Args:
        course_id: Course ID

    Returns:
        Formatted progress
    """
    course = get_course(course_id)
    if not course:
        return f"❌ Nie znaleziono kursu: {course_id}"

    completed = course["completed_lessons"]
    total = course["total_lessons"]
    progress_pct = (completed / total) * 100 if total > 0 else 0
    progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))

    output = f"""# 📊 Postęp w Kursie

## {course['title']}

**Overall:** {progress_bar} {progress_pct:.0f}% ({completed}/{total} lessons)

**Lekcje:**

"""

    for lesson in course["lessons"]:
        status = "✅" if lesson.get("completed", False) else "⏳"
        current = "👉" if lesson["num"] == course["current_lesson"] else "  "

        output += f"""{current} {status} Lekcja {lesson['num']}: {lesson['concept_name']} ({lesson['category']})
"""

    output += f"""
**Statystyki:**
- Ukończone: {completed}
- Pozostałe: {total - completed}
- Czas pozostały: ~{(course['estimated_hours'] * (1 - progress_pct/100)):.1f}h

**Następna akcja:**
`/course continue {course_id}` - Kontynuuj naukę!
"""

    return output


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test lesson conductor"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: lesson_conductor.py <course-id>")
        return

    course_id = sys.argv[1]

    # Show progress
    print(show_course_progress(course_id))


if __name__ == "__main__":
    main()
