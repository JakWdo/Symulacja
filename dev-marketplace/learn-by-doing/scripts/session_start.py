#!/usr/bin/env python3
"""
SessionStart Hook - Wyświetla welcome message i status uczenia się

Funkcjonalność:
- Podstawowy welcome message
- Licznik sesji i streak
- Spaced repetition (koncepty do powtórki)
- Daily goals
- Statystyki postępów
"""
import json
import sys
from pathlib import Path

# Import data_manager
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import (
    load_progress,
    save_progress,
    load_config,
    load_learning_prompt,
    update_session_count,
    get_concepts_to_review,
    format_concepts_for_review,
    ensure_data_files_exist
)


def generate_daily_goals(progress: dict, config: dict) -> list:
    """
    Generuj cele na dzisiaj

    Args:
        progress: Dict z postępem
        config: Dict z konfiguracją

    Returns:
        Lista string-ów z celami
    """
    session_num = progress.get("sessions", 0)

    goals = [
        "✍️ Pisz kod z TODO(human) - praktyka czyni mistrza",
        "💡 Pytaj 'dlaczego' gdy coś jest niejasne",
        "🔗 Szukaj podobnych patternów w innych częściach Sight"
    ]

    # Co 5 sesji - quiz reminder
    quiz_interval = config.get("daily_goals", {}).get("quiz_every_n_sessions", 5)
    if session_num > 0 and session_num % quiz_interval == 0:
        goals.insert(0, "🎯 Dzisiaj: Test wiedzy (/quiz) - sprawdź co pamiętasz!")

    return goals


def format_welcome_message(progress: dict, config: dict, to_review: list, learning_prompt: str) -> str:
    """
    Formatuj pełny welcome message

    Args:
        progress: Dict z postępem
        config: Dict z konfiguracją
        to_review: Lista konceptów do powtórki
        learning_prompt: String z głównym promptem uczącym

    Returns:
        Sformatowany string z welcome message
    """
    session_num = progress.get("sessions", 0)
    streak = progress.get("streak_days", 0)
    streak_emoji = "🔥" if streak >= 3 else "⭐" if streak > 0 else "💤"

    # Statystyki
    total_concepts = len(progress.get("concepts", {}))
    mastered_concepts = sum(
        1 for c in progress.get("concepts", {}).values()
        if c.get("mastery_level", 0) >= 3
    )

    current_focus = progress.get("current_focus", {})
    focus_category = current_focus.get("category", "Backend (FastAPI + PostgreSQL)")

    # Daily goals
    goals = generate_daily_goals(progress, config)
    goals_str = "\n".join(f"  {goal}" for goal in goals)

    # Concepts to review
    review_str = format_concepts_for_review(to_review)

    # Build message
    message = f"""
{learning_prompt}

---

# 🎓 SESJA UCZENIA #{session_num}

## Twoje Statystyki:
- {streak_emoji} **Passa:** {streak} dni pod rząd
- 📊 **Opanowane koncepty:** {mastered_concepts}/{total_concepts}
- 🎯 **Obecny focus:** {focus_category}

## Dzisiejsze Cele:
{goals_str}

## Do Powtórki (Spaced Repetition):
{review_str}

---

**PAMIĘTAJ:** Tryb nauczania jest aktywny! Będę wyjaśniał, pozostawiał TODO(human) i pytał o zrozumienie.
Możesz używać komend: /learn, /review, /progress, /concepts

Szczęśliwego kodowania! 🚀
"""

    return message.strip()


def main():
    """Główna funkcja SessionStart hook"""
    try:
        # Ensure data files exist
        ensure_data_files_exist()

        # Load data
        progress = load_progress()
        config = load_config()
        learning_prompt = load_learning_prompt()

        # Update session count and streak
        progress = update_session_count(progress)
        save_progress(progress)

        # Get concepts to review (if spaced repetition enabled)
        to_review = []
        if config.get("spaced_repetition", {}).get("enabled", True):
            to_review = get_concepts_to_review(progress, config)

        # Format welcome message
        message = format_welcome_message(progress, config, to_review, learning_prompt)

        # Output for Claude Code hook
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": message
            }
        }

        print(json.dumps(output, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        # Graceful fallback - show simple message
        simple_message = """
🎓 TRYB NAUCZANIA AKTYWNY - Projekt Sight

Będę Ci pomagał przez:
- 💡 Wyjaśnianie DLACZEGO coś działa (nie tylko JAK)
- ✍️ Zostawianie TODO(human) do samodzielnej implementacji
- 🔗 Pokazywanie powiązań między konceptami w Sight
- 🤔 Zadawanie pytań do refleksji

Dostępne komendy: /learn, /review, /progress, /concepts

Szczęśliwego kodowania! 🚀

⚠️ Uwaga: Wystąpił błąd przy ładowaniu pełnych statystyk. Plugin działa w trybie uproszczonym.
"""
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": simple_message.strip()
            }
        }

        print(json.dumps(output, ensure_ascii=False), file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
