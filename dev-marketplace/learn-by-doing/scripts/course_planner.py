#!/usr/bin/env python3
"""
Course Planner - Interactive Course Creation

Odpowiedzialności:
- Pyta użytkownika o preferencje (poziom, czas, styl)
- Tworzy spersonalizowane plany kursów
- Generuje lekcje z teoria + TODO(human)
- Mapuje cele na koncepty z knowledge_base

Universal Learning System v2.3
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_knowledge_base, load_learning_domains

logger = logging.getLogger(__name__)


# ============================================================================
# COURSE PLANNING
# ============================================================================

def ask_user_preferences() -> Dict[str, str]:
    """
    Pyta użytkownika o preferencje nauki

    Returns:
        Dict z: level, time, style
    """
    print("# 🎓 Tworzę spersonalizowany kurs!")
    print()
    print("Najpierw kilka pytań:")
    print()

    # Level
    print("## 1. Jaki masz poziom?")
    print()
    print("- **beginner** - Dopiero zaczynasz (wyjaśnię podstawy)")
    print("- **intermediate** - Znasz podstawy (skupimy się na praktyce)")
    print("- **advanced** - Jesteś zaawansowany (głębokie dive, best practices)")
    print()
    level = input("Wybierz (beginner/intermediate/advanced): ").strip().lower()
    if level not in ["beginner", "intermediate", "advanced"]:
        level = "intermediate"  # default
    print()

    # Time
    print("## 2. Ile masz czasu?")
    print()
    print("- **quick** (~2-3h) - Szybki przegląd, podstawy")
    print("- **standard** (~8-10h) - Standardowy kurs, balanced")
    print("- **deep** (~20-30h) - Głębokie zanurzenie, mastery")
    print()
    time = input("Wybierz (quick/standard/deep): ").strip().lower()
    if time not in ["quick", "standard", "deep"]:
        time = "standard"  # default
    print()

    # Style
    print("## 3. Preferowany styl nauki?")
    print()
    print("- **theory-first** - Najpierw teoria, potem praktyka")
    print("- **practice-first** - Najpierw praktyka, teoria po drodze")
    print("- **balanced** - Mix teorii i praktyki")
    print()
    style = input("Wybierz (theory-first/practice-first/balanced): ").strip().lower()
    if style not in ["theory-first", "practice-first", "balanced"]:
        style = "balanced"  # default
    print()

    return {
        "level": level,
        "time": time,
        "style": style
    }


def extract_concepts_from_goal(goal: str, domain_id: str = "software-engineering") -> List[str]:
    """
    Wyciąga koncepty z celu na podstawie knowledge_base

    Args:
        goal: Cel użytkownika (np. "Dodaj ML do projektu")
        domain_id: ID dziedziny (default: software-engineering)

    Returns:
        Lista concept IDs
    """
    knowledge_base = load_knowledge_base()
    concepts = knowledge_base.get("concepts", {})

    # Simple keyword matching
    goal_lower = goal.lower()
    matched_concepts = []

    for concept_id, concept_data in concepts.items():
        concept_name = concept_data.get("name", "").lower()
        category = concept_data.get("category", "").lower()
        use_cases = " ".join(concept_data.get("use_cases", [])).lower()

        # Check if concept is relevant to goal
        if (concept_name in goal_lower or
            category in goal_lower or
            any(keyword in goal_lower for keyword in concept_name.split())):
            matched_concepts.append(concept_id)

    # Keywords → concepts mapping
    keyword_map = {
        "ml": ["langchain-chains", "vector-embeddings", "rag"],
        "machine learning": ["langchain-chains", "vector-embeddings", "rag"],
        "frontend": ["react-components", "react-hooks", "tanstack-query", "typescript-basics"],
        "backend": ["fastapi-routing", "fastapi-async", "sqlalchemy-models"],
        "database": ["sqlalchemy-models", "sqlalchemy-async", "alembic-migrations"],
        "docker": ["docker-compose", "docker-multistage"],
        "testing": ["pytest-testing", "pytest-fixtures", "pytest-async"],
        "api": ["fastapi-routing", "fastapi-async", "fastapi-di"],
        "cache": ["redis-caching"],
        "graph": ["neo4j-graph"],
        "rag": ["vector-embeddings", "vector-search", "rag", "hybrid-search"],
    }

    for keyword, concept_ids in keyword_map.items():
        if keyword in goal_lower:
            matched_concepts.extend(concept_ids)

    # Remove duplicates, keep order
    seen = set()
    unique_concepts = []
    for cid in matched_concepts:
        if cid not in seen and cid in concepts:
            seen.add(cid)
            unique_concepts.append(cid)

    return unique_concepts[:10]  # Limit to 10 concepts max


def create_course_plan(
    goal: str,
    preferences: Dict[str, str],
    domain_id: str = "software-engineering"
) -> Dict[str, Any]:
    """
    Tworzy plan kursu na podstawie celu i preferencji

    Args:
        goal: Cel użytkownika
        preferences: Dict z level, time, style
        domain_id: ID dziedziny

    Returns:
        Dict z course plan (lessons, metadata)
    """
    level = preferences.get("level", "intermediate")
    time = preferences.get("time", "standard")
    style = preferences.get("style", "balanced")

    # Extract concepts from goal
    concept_ids = extract_concepts_from_goal(goal, domain_id)

    if not concept_ids:
        logger.warning(f"No concepts found for goal: {goal}")
        return None

    # Load knowledge base for concept details
    knowledge_base = load_knowledge_base()
    concepts = knowledge_base.get("concepts", {})

    # Determine number of lessons based on time
    lessons_count = {
        "quick": min(3, len(concept_ids)),
        "standard": min(5, len(concept_ids)),
        "deep": min(8, len(concept_ids)),
    }[time]

    # Select concepts for lessons (prioritize prerequisites)
    selected_concepts = concept_ids[:lessons_count]

    # Generate lessons
    lessons = []
    for i, concept_id in enumerate(selected_concepts, 1):
        concept = concepts.get(concept_id, {})

        lesson = {
            "num": i,
            "concept_id": concept_id,
            "concept_name": concept.get("name", concept_id),
            "category": concept.get("category", "General"),
            "theory": generate_theory(concept, level, style),
            "todo_human": generate_todo_human(concept, level, style, goal),
            "estimated_time_minutes": estimate_lesson_time(level, time),
            "completed": False
        }
        lessons.append(lesson)

    # Create course plan
    course_plan = {
        "goal": goal,
        "level": level,
        "time_budget": time,
        "style": style,
        "domain_id": domain_id,
        "total_lessons": lessons_count,
        "lessons": lessons,
        "estimated_hours": sum(l["estimated_time_minutes"] for l in lessons) / 60
    }

    return course_plan


def generate_theory(concept: Dict, level: str, style: str) -> str:
    """
    Generuje teorię dla lekcji

    Args:
        concept: Concept data z knowledge_base
        level: beginner/intermediate/advanced
        style: theory-first/practice-first/balanced

    Returns:
        Theory text
    """
    name = concept.get("name", "Unknown")
    description = concept.get("description", "")
    use_cases = concept.get("use_cases", [])

    # Adjust depth based on level
    if level == "beginner":
        depth = "Wyjaśnię od podstaw"
    elif level == "intermediate":
        depth = "Zakładam że znasz podstawy"
    else:
        depth = "Głębokie dive w zaawansowane aspekty"

    theory = f"""💡 Koncept: **{name}**

{description}

**{depth}**

📝 Zastosowania:
{chr(10).join(f'- {uc}' for uc in use_cases[:3])}

**Dlaczego to ważne:**
{concept.get('why_important', 'Ten koncept jest fundamentalny dla projektu.')}
"""

    return theory


def generate_todo_human(concept: Dict, level: str, style: str, goal: str) -> str:
    """
    Generuje TODO(human) dla lekcji

    Args:
        concept: Concept data
        level: beginner/intermediate/advanced
        style: Learning style
        goal: User goal

    Returns:
        TODO(human) text
    """
    name = concept.get("name", "Unknown")

    # Difficulty emoji
    difficulty = {
        "beginner": "🟢",
        "intermediate": "🟡",
        "advanced": "🔴"
    }[level]

    todo = f"""🛠️ TODO(human) {difficulty}: Praktyczne zadanie

**Zadanie:** Zaimplementuj {name} w kontekście: "{goal}"

**Podpowiedź:**
{concept.get('hint', f'Sprawdź dokumentację {name} i zacznij od prostego przykładu.')}

**Oczekiwane:**
- ~{estimate_task_lines(level)} linii kodu
- Czas: ~{estimate_lesson_time(level, 'standard')} minut
- Plik: {suggest_file_path(concept, goal)}

**Koncepty:**
{name}, {concept.get('category', 'General')}

**Gotowy?** Powiedz "done" gdy skończysz!
"""

    return todo


def estimate_lesson_time(level: str, time_budget: str) -> int:
    """
    Szacuje czas lekcji w minutach

    Args:
        level: beginner/intermediate/advanced
        time_budget: quick/standard/deep

    Returns:
        Minutes
    """
    base_time = {
        "quick": 30,
        "standard": 90,
        "deep": 180
    }[time_budget]

    # Adjust for level
    multiplier = {
        "beginner": 1.2,
        "intermediate": 1.0,
        "advanced": 0.8
    }[level]

    return int(base_time * multiplier)


def estimate_task_lines(level: str) -> str:
    """Szacuje linii kodu dla TODO(human)"""
    return {
        "beginner": "10-20",
        "intermediate": "20-50",
        "advanced": "50-100"
    }[level]


def suggest_file_path(concept: Dict, goal: str) -> str:
    """Sugeruje ścieżkę pliku dla TODO"""
    category = concept.get("category", "general").lower()

    paths = {
        "backend": "app/services/",
        "frontend": "frontend/src/components/",
        "database": "app/models/",
        "ai/ml": "app/services/ai/",
        "devops": "docker/",
        "testing": "tests/"
    }

    return paths.get(category, "app/") + "your_file.py"


def format_course_preview(course_plan: Dict) -> str:
    """
    Formatuje preview kursu do wyświetlenia

    Args:
        course_plan: Course plan dict

    Returns:
        Formatted string
    """
    lessons = course_plan.get("lessons", [])
    total_hours = course_plan.get("estimated_hours", 0)

    preview = f"""# ✅ Kurs Gotowy!

## 📚 "{course_plan.get('goal')}"

**Parametry:**
- Poziom: {course_plan.get('level')}
- Czas: {course_plan.get('time_budget')} (~{total_hours:.1f}h)
- Styl: {course_plan.get('style')}

**Lekcje ({len(lessons)}):**

"""

    for lesson in lessons:
        preview += f"""Lekcja {lesson['num']}: {lesson['concept_name']} ({lesson['category']})
  ⏱️ ~{lesson['estimated_time_minutes']} min

"""

    preview += f"""
**Łączny czas:** ~{total_hours:.1f}h

Zaczynamy? (Powiedz "yes" aby rozpocząć Lekcję 1)
"""

    return preview


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test course planner"""
    print("# 🎓 Course Planner Test")
    print()

    # Simulate user goal
    goal = input("Co chcesz się nauczyć? (np. 'Dodaj ML do projektu'): ").strip()
    if not goal:
        goal = "Dodaj ML recommendations do projektu"

    # Ask preferences
    preferences = ask_user_preferences()

    # Create course plan
    print("Tworzę plan kursu...")
    print()
    course_plan = create_course_plan(goal, preferences)

    if not course_plan:
        print("❌ Nie udało się stworzyć kursu (brak konceptów)")
        return

    # Show preview
    print(format_course_preview(course_plan))


if __name__ == "__main__":
    main()
