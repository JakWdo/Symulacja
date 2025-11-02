#!/usr/bin/env python3
"""
Lightweight Progress Tracker - Course-only tracking

Funkcjonalność:
- Tracking ukończonych lekcji w kursach
- Obliczanie progress % per kurs
- Proste obliczanie domain progress (based on courses)
- Bez practice_log, pattern matching, mastery levels

Usage:
    from progress_tracker import ProgressTracker

    tracker = ProgressTracker()
    tracker.mark_lesson_completed("course_001", 1)
    progress = tracker.get_domain_progress("backend")
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Lightweight progress tracker - tylko kursy
    """

    def __init__(self):
        """Inicjalizuj tracker"""
        self.plugin_root = Path(__file__).parent.parent
        self.courses_file = self.plugin_root / "data" / "active_courses.json"
        self.domains_file = self.plugin_root / "data" / "domains.json"

        self.courses = self._load_courses()
        self.domains = self._load_domains()

    def _load_courses(self) -> Dict[str, Any]:
        """Załaduj aktywne kursy"""
        try:
            if not self.courses_file.exists():
                return {"courses": []}

            with open(self.courses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            return {"courses": []}

    def _load_domains(self) -> Dict[str, Any]:
        """Załaduj dziedziny"""
        try:
            if not self.domains_file.exists():
                return {"active_domain": None, "domains": {}}

            with open(self.domains_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading domains: {e}")
            return {"active_domain": None, "domains": {}}

    def _save_courses(self) -> bool:
        """Zapisz kursy do pliku"""
        try:
            self.courses_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.courses_file, 'w', encoding='utf-8') as f:
                json.dump(self.courses, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"Error saving courses: {e}")
            return False

    def _save_domains(self) -> bool:
        """Zapisz dziedziny do pliku"""
        try:
            self.domains_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.domains_file, 'w', encoding='utf-8') as f:
                json.dump(self.domains, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"Error saving domains: {e}")
            return False

    def mark_lesson_completed(self, course_id: str, lesson_id: int) -> bool:
        """
        Oznacz lekcję jako ukończoną

        Args:
            course_id: ID kursu
            lesson_id: ID lekcji (0-indexed)

        Returns:
            True jeśli sukces
        """
        course = self._find_course(course_id)
        if not course:
            logger.warning(f"Course {course_id} not found")
            return False

        lessons = course.get('lessons', [])
        if lesson_id >= len(lessons):
            logger.warning(f"Lesson {lesson_id} not found in course {course_id}")
            return False

        # Mark lesson completed
        lesson = lessons[lesson_id]
        lesson['status'] = 'completed'
        lesson['completed_at'] = datetime.now(timezone.utc).isoformat()

        # Update course progress
        total = len(lessons)
        completed = sum(1 for l in lessons if l.get('status') == 'completed')
        course['progress'] = (completed / total) * 100 if total > 0 else 0
        course['current_lesson'] = min(lesson_id + 1, total - 1)

        # Save
        success = self._save_courses()

        if success:
            # Update domain stats
            domain_id = course.get('domain')
            if domain_id:
                self.update_domain_stats(domain_id)

        return success

    def get_active_courses(self) -> List[Dict[str, Any]]:
        """
        Zwróć listę aktywnych kursów

        Returns:
            Lista kursów
        """
        return self.courses.get('courses', [])

    def get_domain_progress(self, domain_id: str) -> Dict[str, Any]:
        """
        Zwróć statystyki dziedziny

        Args:
            domain_id: ID dziedziny

        Returns:
            Dict z total, mastered, progress_pct
        """
        domain = self.domains.get('domains', {}).get(domain_id)
        if not domain:
            return {'total': 0, 'mastered': 0, 'progress_pct': 0}

        concepts = domain.get('concepts', [])
        total = len(concepts)

        # Count mastered concepts
        mastered = self._count_mastered_in_domain(domain_id)

        return {
            'total': total,
            'mastered': mastered,
            'progress_pct': (mastered / total * 100) if total > 0 else 0
        }

    def update_domain_stats(self, domain_id: str) -> bool:
        """
        Przelicz statystyki dziedziny

        Args:
            domain_id: ID dziedziny

        Returns:
            True jeśli sukces
        """
        domain = self.domains.get('domains', {}).get(domain_id)
        if not domain:
            return False

        # Recalculate
        concepts = domain.get('concepts', [])
        mastered = self._count_mastered_in_domain(domain_id)

        # Update
        domain['concepts_count'] = len(concepts)
        domain['mastered_count'] = mastered
        domain['last_updated'] = datetime.now(timezone.utc).isoformat()

        return self._save_domains()

    def _find_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Znajdź kurs po ID

        Args:
            course_id: ID kursu

        Returns:
            Dict z kursem lub None
        """
        for course in self.courses.get('courses', []):
            if course.get('id') == course_id:
                return course
        return None

    def _count_mastered_in_domain(self, domain_id: str) -> int:
        """
        Policz opanowane koncepty w dziedzinie

        Logika: Koncept jest "mastered" jeśli pojawił się w 3+ ukończonych lekcjach

        Args:
            domain_id: ID dziedziny

        Returns:
            Liczba opanowanych konceptów
        """
        concept_appearances = {}

        # Iterate through courses in this domain
        for course in self.courses.get('courses', []):
            if course.get('domain') != domain_id:
                continue

            # Count concept appearances in completed lessons
            for lesson in course.get('lessons', []):
                if lesson.get('status') == 'completed':
                    for concept in lesson.get('concepts_covered', []):
                        concept_appearances[concept] = concept_appearances.get(concept, 0) + 1

        # Count mastered (appeared 3+ times)
        return sum(1 for count in concept_appearances.values() if count >= 3)


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test progress tracker"""
    print("Testing progress_tracker.py...")

    tracker = ProgressTracker()

    # Get active courses
    courses = tracker.get_active_courses()
    print(f"\n✅ Active courses: {len(courses)}")

    # Get domain progress
    progress = tracker.get_domain_progress("backend")
    print(f"\n📊 Backend progress: {progress['mastered']}/{progress['total']} ({progress['progress_pct']:.0f}%)")

    # Test mark lesson completed (mock)
    if courses:
        first_course = courses[0]
        course_id = first_course.get('id')
        print(f"\n🧪 Testing mark_lesson_completed for course {course_id}...")

        success = tracker.mark_lesson_completed(course_id, 0)
        if success:
            print("✅ Lesson marked completed")
        else:
            print("❌ Failed to mark lesson")
    else:
        print("\n⚠️  No courses to test with")

    print("\n✅ Tests completed")
