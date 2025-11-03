#!/usr/bin/env python3
"""
Course Manager - CRUD Operations for Courses

Odpowiedzialności:
- Zapisywanie i ładowanie kursów z courses.json
- Aktualizacja postępu (completed lessons)
- Lista aktywnych kursów
- Usuwanie ukończonych kursów

Universal Learning System v2.3
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Import data_manager for storage path
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import DATA_DIR

logger = logging.getLogger(__name__)


# ============================================================================
# DATA PATHS
# ============================================================================

def get_courses_file() -> Path:
    """Get path to courses.json"""
    return DATA_DIR / "courses.json"


# ============================================================================
# CRUD OPERATIONS
# ============================================================================

def load_courses() -> Dict[str, Any]:
    """
    Ładuje wszystkie kursy z courses.json

    Returns:
        Dict z active_courses list
    """
    courses_file = get_courses_file()

    if not courses_file.exists():
        # Initialize empty
        return {
            "active_courses": [],
            "completed_courses": [],
            "version": "2.3"
        }

    try:
        with open(courses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Error loading courses: {e}")
        return {
            "active_courses": [],
            "completed_courses": [],
            "version": "2.3"
        }


def save_courses(courses_data: Dict[str, Any]) -> bool:
    """
    Zapisuje kursy do courses.json

    Args:
        courses_data: Dict z active_courses, completed_courses

    Returns:
        True jeśli sukces
    """
    courses_file = get_courses_file()

    try:
        courses_file.parent.mkdir(parents=True, exist_ok=True)

        with open(courses_file, 'w', encoding='utf-8') as f:
            json.dump(courses_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved courses to {courses_file}")
        return True

    except Exception as e:
        logger.error(f"Error saving courses: {e}")
        return False


def create_course(course_plan: Dict[str, Any]) -> str:
    """
    Tworzy nowy kurs z planu

    Args:
        course_plan: Plan kursu z course_planner

    Returns:
        Course ID
    """
    courses_data = load_courses()

    # Generate course ID (slug from goal)
    goal = course_plan.get("goal", "unnamed-course")
    course_id = goal.lower()
    course_id = course_id.replace(" ", "-")
    course_id = course_id.replace("?", "")
    course_id = course_id[:50]  # Limit length

    # Check if ID already exists
    existing_ids = [c["id"] for c in courses_data["active_courses"]]
    if course_id in existing_ids:
        # Append timestamp
        course_id = f"{course_id}-{int(datetime.now(timezone.utc).timestamp())}"

    # Create course object
    course = {
        "id": course_id,
        "title": course_plan.get("goal"),
        "level": course_plan.get("level"),
        "time_budget": course_plan.get("time_budget"),
        "style": course_plan.get("style"),
        "domain_id": course_plan.get("domain_id", "software-engineering"),
        "lessons": course_plan.get("lessons", []),
        "current_lesson": 1,
        "total_lessons": course_plan.get("total_lessons"),
        "completed_lessons": 0,
        "estimated_hours": course_plan.get("estimated_hours"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }

    # Add to active courses
    courses_data["active_courses"].append(course)

    # Save
    save_courses(courses_data)

    logger.info(f"Created course: {course_id}")
    return course_id


def get_course(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Pobiera kurs po ID

    Args:
        course_id: Course ID

    Returns:
        Course dict lub None
    """
    courses_data = load_courses()

    for course in courses_data["active_courses"]:
        if course["id"] == course_id:
            return course

    return None


def list_active_courses() -> List[Dict[str, Any]]:
    """
    Lista wszystkich aktywnych kursów

    Returns:
        List of course dicts
    """
    courses_data = load_courses()
    return courses_data.get("active_courses", [])


def update_lesson_progress(course_id: str, lesson_num: int, completed: bool = True) -> bool:
    """
    Aktualizuje postęp lekcji

    Args:
        course_id: Course ID
        lesson_num: Numer lekcji (1-indexed)
        completed: Czy ukończona

    Returns:
        True jeśli sukces
    """
    courses_data = load_courses()

    for course in courses_data["active_courses"]:
        if course["id"] == course_id:
            # Find lesson
            for lesson in course["lessons"]:
                if lesson["num"] == lesson_num:
                    lesson["completed"] = completed

                    if completed:
                        lesson["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Update completed count
            course["completed_lessons"] = sum(
                1 for l in course["lessons"] if l.get("completed", False)
            )

            # Update current lesson (next uncompleted)
            for lesson in course["lessons"]:
                if not lesson.get("completed", False):
                    course["current_lesson"] = lesson["num"]
                    break
            else:
                # All lessons completed
                course["current_lesson"] = course["total_lessons"]
                course["status"] = "completed"

            # Update timestamp
            course["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Save
            save_courses(courses_data)
            logger.info(f"Updated lesson {lesson_num} in course {course_id}")
            return True

    logger.warning(f"Course {course_id} not found")
    return False


def move_to_completed(course_id: str) -> bool:
    """
    Przenosi kurs do completed_courses

    Args:
        course_id: Course ID

    Returns:
        True jeśli sukces
    """
    courses_data = load_courses()

    for i, course in enumerate(courses_data["active_courses"]):
        if course["id"] == course_id:
            # Remove from active
            completed_course = courses_data["active_courses"].pop(i)

            # Mark as completed
            completed_course["status"] = "completed"
            completed_course["completed_at"] = datetime.now(timezone.utc).isoformat()

            # Add to completed
            if "completed_courses" not in courses_data:
                courses_data["completed_courses"] = []

            courses_data["completed_courses"].append(completed_course)

            # Save
            save_courses(courses_data)
            logger.info(f"Moved course {course_id} to completed")
            return True

    return False


def remove_course(course_id: str) -> bool:
    """
    Usuwa kurs (z active lub completed)

    Args:
        course_id: Course ID

    Returns:
        True jeśli sukces
    """
    courses_data = load_courses()

    # Try active first
    for i, course in enumerate(courses_data["active_courses"]):
        if course["id"] == course_id:
            courses_data["active_courses"].pop(i)
            save_courses(courses_data)
            logger.info(f"Removed active course {course_id}")
            return True

    # Try completed
    for i, course in enumerate(courses_data.get("completed_courses", [])):
        if course["id"] == course_id:
            courses_data["completed_courses"].pop(i)
            save_courses(courses_data)
            logger.info(f"Removed completed course {course_id}")
            return True

    return False


def get_next_lesson(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Pobiera następną (niezakończoną) lekcję

    Args:
        course_id: Course ID

    Returns:
        Lesson dict lub None
    """
    course = get_course(course_id)
    if not course:
        return None

    current_lesson_num = course.get("current_lesson", 1)

    for lesson in course["lessons"]:
        if lesson["num"] == current_lesson_num:
            return lesson

    return None


# ============================================================================
# FORMATTING
# ============================================================================

def format_course_summary(course: Dict[str, Any]) -> str:
    """
    Formatuje podsumowanie kursu

    Args:
        course: Course dict

    Returns:
        Formatted string
    """
    progress_pct = (course["completed_lessons"] / course["total_lessons"]) * 100 if course["total_lessons"] > 0 else 0
    progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))

    summary = f"""**{course['title']}** (ID: `{course['id']}`)
  Progress: {progress_bar} {progress_pct:.0f}% ({course['completed_lessons']}/{course['total_lessons']} lessons)
  Current: Lekcja {course['current_lesson']}
  Level: {course['level']} | Time: ~{course['estimated_hours']:.1f}h
  Status: {course['status']}
"""

    return summary


def format_courses_list(courses: List[Dict[str, Any]]) -> str:
    """
    Formatuje listę kursów

    Args:
        courses: Lista kursów

    Returns:
        Formatted string
    """
    if not courses:
        return "📭 Brak aktywnych kursów\n\nUżyj `/course start \"cel\"` aby rozpocząć!"

    output = "# 📚 Twoje Aktywne Kursy\n\n"

    for course in courses:
        output += format_course_summary(course)
        output += "\n"

    output += f"\nŁącznie: {len(courses)} kursów\n"
    output += "\nUżyj `/course continue <id>` aby kontynuować!"

    return output


# ============================================================================
# COURSE LIBRARY
# ============================================================================

def get_course_library_dir() -> Path:
    """Get path to course library directory"""
    plugin_root = Path(__file__).parent.parent
    return plugin_root / "data" / "course_library"


def load_course_library() -> List[Dict[str, Any]]:
    """
    Ładuje wszystkie kursy z course library

    Returns:
        Lista kursów z library (sorted by popularity desc)
    """
    library_dir = get_course_library_dir()

    if not library_dir.exists():
        logger.warning(f"Course library directory not found: {library_dir}")
        return []

    courses = []
    for course_file in library_dir.glob("*.json"):
        try:
            with open(course_file, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
                courses.append(course_data)
        except Exception as e:
            logger.error(f"Error loading course {course_file}: {e}")

    # Sort by popularity (descending)
    courses.sort(key=lambda x: x.get('popularity', 0), reverse=True)

    return courses


def get_library_course(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Pobiera kurs z library po ID

    Args:
        course_id: ID kursu (np. "backend-onboarding")

    Returns:
        Course dict lub None
    """
    courses = load_course_library()

    for course in courses:
        if course.get('id') == course_id:
            return course

    return None


def start_library_course(course_id: str) -> Optional[str]:
    """
    Rozpoczyna kurs z library (kopiuje do active_courses)

    Args:
        course_id: ID kursu z library

    Returns:
        Course ID jeśli sukces, None jeśli błąd
    """
    # Load course from library
    library_course = get_library_course(course_id)

    if not library_course:
        logger.error(f"Course {course_id} not found in library")
        return None

    # Convert to course plan format (compatible with create_course)
    course_plan = {
        "goal": library_course.get("title"),
        "level": library_course.get("level", "intermediate"),
        "time_budget": library_course.get("time_budget", "standard"),
        "style": "balanced",
        "domain_id": library_course.get("domain_id", "software-engineering"),
        "total_lessons": library_course.get("total_lessons"),
        "lessons": library_course.get("lessons", []),
        "estimated_hours": library_course.get("estimated_hours")
    }

    # Create course
    new_course_id = create_course(course_plan)

    logger.info(f"Started library course: {course_id} → {new_course_id}")
    return new_course_id


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test course manager"""
    print("# Course Manager Test")
    print()

    # List courses
    courses = list_active_courses()
    print(format_courses_list(courses))

    # List course library
    print("\n# Course Library:")
    library = load_course_library()
    for course in library:
        print(f"- {course['id']}: {course['title']}")


if __name__ == "__main__":
    main()
