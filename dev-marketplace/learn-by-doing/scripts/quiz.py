#!/usr/bin/env python3
"""
Quiz Command - Sprawdź swoją wiedzę

Usage:
    /quiz                    # Start quiz (active domain)
    /quiz <domain-id>        # Start quiz for specific domain
    /quiz --show-answers     # Show answers for last quiz (learning mode)

Universal Learning System v2.0
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_knowledge_base
from domain_manager import get_active_domain, get_domain
from quiz_generator import generate_quiz, format_quiz_for_display


def start_quiz(domain_id: str, domain_name: str, num_questions: int = 5):
    """
    Rozpocznij quiz dla danej dziedziny

    Args:
        domain_id: ID dziedziny
        domain_name: Nazwa dziedziny
        num_questions: Liczba pytań
    """
    print(f"# 🎯 Quiz: **{domain_name}**")
    print()

    # Load data
    progress = load_progress()
    kb = load_knowledge_base()

    # Generate quiz
    questions = generate_quiz(progress, kb, domain_id, num_questions)

    if not questions:
        print("❌ **Brak pytań do wygenerowania**")
        print()
        print("Powody:")
        print("- Brak practiced concepts w tej dziedzinie")
        print("- Za mało praktyki (min. 1 akcja per koncept)")
        print()
        print(f"💡 **Tip:** Zacznij pracować nad zadaniami z **{domain_name}**,")
        print("a system automatycznie wykryje koncepty i wygeneruje quiz!")
        return

    # Display quiz
    print(format_quiz_for_display(questions))

    # Save quiz to temp file for answer checking
    quiz_file = Path.home() / ".claude" / "learn-by-doing" / "last_quiz.json"
    quiz_file.parent.mkdir(exist_ok=True, parents=True)

    quiz_data = {
        "domain_id": domain_id,
        "domain_name": domain_name,
        "questions": questions,
    }

    with open(quiz_file, "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, indent=2, ensure_ascii=False)

    print(f"Quiz zapisany! Odpowiedz na pytania w kolejnej wiadomości.")


def show_quiz_answers():
    """Pokaż odpowiedzi na ostatni quiz (learning mode)"""
    quiz_file = Path.home() / ".claude" / "learn-by-doing" / "last_quiz.json"

    if not quiz_file.exists():
        print("❌ **Brak quizu do wyświetlenia**")
        print()
        print("Użyj `/quiz` aby wygenerować nowy quiz.")
        return

    with open(quiz_file, "r", encoding="utf-8") as f:
        quiz_data = json.load(f)

    questions = quiz_data["questions"]
    domain_name = quiz_data["domain_name"]

    print(f"# 🎓 Odpowiedzi - Quiz: **{domain_name}**")
    print()

    for i, q in enumerate(questions, 1):
        print(f"## Pytanie {i}/{len(questions)}")
        print(f"**Koncept:** {q['concept_name']} ({q['category']})\n")

        if q["type"] == "multiple_choice":
            print(f"**Pytanie:** {q['question']}\n")
            for j, option in enumerate(q["options"]):
                marker = "✅" if j == q["correct_answer"] else "  "
                print(f"{marker} {chr(65 + j)}. {option}")

        elif q["type"] == "true_false":
            print(f"**Stwierdzenie:** {q['statement']}\n")
            correct = "Prawda" if q["correct_answer"] else "Fałsz"
            print(f"✅ Poprawna odpowiedź: **{correct}**")

        elif q["type"] == "fill_in":
            print(f"**Pytanie:** {q['question']}\n")
            print(f"✅ Poprawna odpowiedź: **{q['correct_answer']}**")

        print()
        print("---\n")

    print("## 💡 Jak się uczyć?")
    print()
    print("Jeśli nie znasz odpowiedzi na pytanie:")
    print("1. **Przeczytaj dokumentację** danego konceptu")
    print("2. **Praktykuj** - napisz kod używający tego konceptu")
    print("3. **Spróbuj ponownie** za kilka dni (spaced repetition)")
    print()


def main():
    """Główna funkcja"""
    args = sys.argv[1:]

    # Show answers
    if args and args[0] == "--show-answers":
        show_quiz_answers()
        return

    # Get domain
    if args:
        # Specific domain
        domain_id = args[0]
        domain = get_domain(domain_id)

        if not domain:
            print(f"❌ **Błąd:** Dziedzina '{domain_id}' nie istnieje")
            print()
            print("Użyj `/learn --list` aby zobaczyć dostępne dziedziny.")
            return

        domain_name = domain["name"]
    else:
        # Active domain
        active_domain = get_active_domain()

        if not active_domain:
            print("❌ **Brak aktywnej dziedziny**")
            print()
            print("Użyj `/learn <domain>` aby dodać dziedzinę.")
            return

        domain_id = active_domain.get("id")
        domain_name = active_domain.get("name")

    # Start quiz
    num_questions = 5  # Default
    start_quiz(domain_id, domain_name, num_questions)


if __name__ == "__main__":
    main()
