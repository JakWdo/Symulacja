#!/usr/bin/env python3
"""
Quiz Generator - Generuje pytania testowe z practice log

Funkcjonalność:
- Generowanie pytań z practiced concepts
- 3 typy pytań: multiple choice, fill-in, true/false
- Trudność bazowana na mastery level
- Zapisywanie wyników do practice_log

Universal Learning System v2.0
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_knowledge_base, append_practice_log, load_learning_domains
from domain_manager import get_active_domain


# ============================================================================
# QUIZ QUESTION TEMPLATES
# ============================================================================

QUESTION_TEMPLATES = {
    "multiple_choice": [
        {
            "question": "Co to jest {concept}?",
            "type": "definition",
        },
        {
            "question": "Kiedy używamy {concept}?",
            "type": "usage",
        },
        {
            "question": "Jaka jest główna korzyść z {concept}?",
            "type": "benefit",
        },
    ],
    "true_false": [
        {
            "statement": "{concept} jest używany do {false_purpose}",
            "answer": False,
        },
        {
            "statement": "{concept} poprawia {benefit}",
            "answer": True,
        },
    ],
    "fill_in": [
        {
            "question": "{concept} pozwala na _____ w projekcie",
            "type": "completion",
        },
    ],
}


# ============================================================================
# QUIZ GENERATION
# ============================================================================

def get_practiced_concepts(progress: Dict[str, Any], domain_id: Optional[str] = None, min_practice: int = 3) -> List[Dict[str, Any]]:
    """
    Pobierz koncepty które użytkownik praktykował

    Args:
        progress: Dict z postępem
        domain_id: ID dziedziny (opcjonalne - filtruj po domenie)
        min_practice: Minimalna liczba praktyk

    Returns:
        Lista konceptów do quizu
    """
    concepts = progress.get("concepts", {})
    practiced = []

    for concept_id, concept_data in concepts.items():
        practice_count = concept_data.get("practice_count", 0)
        mastery = concept_data.get("mastery_level", 0)

        # Filter by domain if specified
        if domain_id and concept_data.get("domain") != domain_id:
            continue

        # Only concepts with some practice
        if practice_count >= min_practice:
            practiced.append({
                "id": concept_id,
                "name": concept_data.get("name", concept_id),
                "mastery_level": mastery,
                "practice_count": practice_count,
                "category": concept_data.get("category", "Unknown"),
            })

    # Sort by practice_count (most practiced first, but randomize a bit)
    practiced.sort(key=lambda x: x["practice_count"] + random.randint(-2, 2), reverse=True)

    return practiced


def generate_multiple_choice_question(concept: Dict[str, Any], knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generuj pytanie multiple choice

    Args:
        concept: Dict z konceptem
        knowledge_base: Knowledge base (dla similar concepts jako distractors)

    Returns:
        Dict z pytaniem
    """
    concept_name = concept["name"]
    category = concept["category"]

    # Simple template-based question
    template = random.choice(QUESTION_TEMPLATES["multiple_choice"])

    question_text = template["question"].format(concept=concept_name)

    # Generate options (1 correct + 3 distractors)
    correct_answer = f"Poprawna odpowiedź o {concept_name}"  # Simplified

    # Distractors (simplified - in real scenario, use similar concepts from KB)
    distractors = [
        f"Niepoprawna odpowiedź A",
        f"Niepoprawna odpowiedź B",
        f"Niepoprawna odpowiedź C",
    ]

    options = [correct_answer] + distractors[:3]
    random.shuffle(options)

    correct_index = options.index(correct_answer)

    return {
        "type": "multiple_choice",
        "question": question_text,
        "options": options,
        "correct_answer": correct_index,
        "concept_id": concept["id"],
        "concept_name": concept_name,
        "category": category,
        "difficulty": concept["mastery_level"],
    }


def generate_true_false_question(concept: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generuj pytanie true/false

    Args:
        concept: Dict z konceptem

    Returns:
        Dict z pytaniem
    """
    concept_name = concept["name"]
    category = concept["category"]

    # Random true or false
    is_true = random.choice([True, False])

    if is_true:
        statement = f"{concept_name} jest używany w kategorii {category}"
        answer = True
    else:
        wrong_categories = ["Backend", "Frontend", "Database", "AI/ML", "DevOps", "Testing"]
        if category in wrong_categories:
            wrong_categories.remove(category)
        wrong_category = random.choice(wrong_categories)
        statement = f"{concept_name} jest używany głównie w kategorii {wrong_category}"
        answer = False

    return {
        "type": "true_false",
        "statement": statement,
        "correct_answer": answer,
        "concept_id": concept["id"],
        "concept_name": concept_name,
        "category": category,
        "difficulty": concept["mastery_level"],
    }


def generate_fill_in_question(concept: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generuj pytanie fill-in-the-blank

    Args:
        concept: Dict z konceptem

    Returns:
        Dict z pytaniem
    """
    concept_name = concept["name"]
    category = concept["category"]

    question = f"Koncept _____ należy do kategorii {category}"
    answer = concept_name

    return {
        "type": "fill_in",
        "question": question,
        "correct_answer": answer,
        "concept_id": concept["id"],
        "concept_name": concept_name,
        "category": category,
        "difficulty": concept["mastery_level"],
    }


def generate_quiz(
    progress: Dict[str, Any],
    knowledge_base: Dict[str, Any],
    domain_id: Optional[str] = None,
    num_questions: int = 5,
    question_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generuj pełny quiz

    Args:
        progress: Dict z postępem
        knowledge_base: Knowledge base
        domain_id: ID dziedziny (opcjonalne)
        num_questions: Liczba pytań
        question_types: Lista typów pytań (default: all)

    Returns:
        Lista pytań
    """
    if question_types is None:
        question_types = ["multiple_choice", "true_false", "fill_in"]

    # Get practiced concepts
    practiced = get_practiced_concepts(progress, domain_id, min_practice=1)

    if not practiced:
        return []

    # Select random concepts (max num_questions)
    selected_concepts = random.sample(practiced, min(num_questions, len(practiced)))

    # Generate questions
    questions = []
    for concept in selected_concepts:
        # Random question type
        q_type = random.choice(question_types)

        if q_type == "multiple_choice":
            question = generate_multiple_choice_question(concept, knowledge_base)
        elif q_type == "true_false":
            question = generate_true_false_question(concept)
        elif q_type == "fill_in":
            question = generate_fill_in_question(concept)
        else:
            continue

        questions.append(question)

    return questions


# ============================================================================
# QUIZ RESULTS
# ============================================================================

def save_quiz_result(
    domain_id: str,
    questions: List[Dict[str, Any]],
    user_answers: List[Any],
    score: float
) -> bool:
    """
    Zapisz wynik quizu do practice_log

    Args:
        domain_id: ID dziedziny
        questions: Lista pytań
        user_answers: Lista odpowiedzi użytkownika
        score: Wynik (0.0 - 1.0)

    Returns:
        True jeśli sukces
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "quiz_result",
        "quiz": {
            "domain": domain_id,
            "num_questions": len(questions),
            "score": score,
            "questions": [
                {
                    "concept_id": q["concept_id"],
                    "concept_name": q["concept_name"],
                    "type": q["type"],
                    "correct": user_answers[i] == q.get("correct_answer"),
                    "difficulty": q["difficulty"],
                }
                for i, q in enumerate(questions)
            ],
        }
    }

    return append_practice_log(log_entry)


def format_quiz_for_display(questions: List[Dict[str, Any]]) -> str:
    """
    Formatuj quiz do wyświetlenia

    Args:
        questions: Lista pytań

    Returns:
        Sformatowany string
    """
    lines = ["# 🎯 QUIZ - Sprawdź Swoją Wiedzę\n"]

    for i, q in enumerate(questions, 1):
        lines.append(f"## Pytanie {i}/{len(questions)}")
        lines.append(f"**Koncept:** {q['concept_name']} ({q['category']})")
        lines.append(f"**Trudność:** {'⭐' * q['difficulty']}\n")

        if q["type"] == "multiple_choice":
            lines.append(f"**Pytanie:** {q['question']}\n")
            for j, option in enumerate(q["options"]):
                lines.append(f"{chr(65 + j)}. {option}")
            lines.append("")

        elif q["type"] == "true_false":
            lines.append(f"**Stwierdzenie:** {q['statement']}\n")
            lines.append("A. Prawda")
            lines.append("B. Fałsz\n")

        elif q["type"] == "fill_in":
            lines.append(f"**Pytanie:** {q['question']}\n")
            lines.append("Odpowiedź: ___________\n")

        lines.append("---\n")

    lines.append("## 📝 Jak odpowiedzieć?")
    lines.append("W kolejnej wiadomości napisz odpowiedzi (np. 'A, B, C, A, B')")
    lines.append("lub użyj `/quiz --show-answers` aby zobaczyć poprawne odpowiedzi.\n")

    return "\n".join(lines)


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test quiz generator"""
    print("Testing quiz_generator.py...\n")

    # Load data
    progress = load_progress()
    kb = load_knowledge_base()
    active_domain = get_active_domain()

    domain_id = active_domain.get("id") if active_domain else None
    domain_name = active_domain.get("name") if active_domain else "Unknown"

    print(f"Active domain: {domain_name} ({domain_id})")
    print()

    # Get practiced concepts
    practiced = get_practiced_concepts(progress, domain_id, min_practice=0)
    print(f"Practiced concepts: {len(practiced)}")

    if not practiced:
        print("No practiced concepts yet. Add some data to learning_progress.json")
        print("\nAdding dummy data for testing...")

        # Add dummy practiced concepts
        progress["concepts"] = {
            "fastapi_routing": {
                "name": "FastAPI Routing",
                "category": "Backend",
                "practice_count": 5,
                "mastery_level": 2,
                "domain": domain_id or "software-engineering",
            },
            "react_hooks": {
                "name": "React Hooks",
                "category": "Frontend",
                "practice_count": 8,
                "mastery_level": 3,
                "domain": domain_id or "software-engineering",
            },
            "pandas_basics": {
                "name": "Pandas Basics",
                "category": "Data Science",
                "practice_count": 3,
                "mastery_level": 1,
                "domain": "data-science",
            },
        }

        practiced = get_practiced_concepts(progress, domain_id, min_practice=0)

    # Generate quiz
    questions = generate_quiz(progress, kb, domain_id, num_questions=3)

    if questions:
        print(f"\n✅ Generated {len(questions)} questions\n")
        print(format_quiz_for_display(questions))
    else:
        print("❌ No questions generated")
