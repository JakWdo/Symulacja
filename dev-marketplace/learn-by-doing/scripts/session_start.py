#!/usr/bin/env python3
"""
SessionStart Hook - Wyświetla welcome message i status uczenia się

Funkcjonalność (Universal Learning System v2.0):
- Podstawowy welcome message
- Multi-domain support
- Licznik sesji i streak
- Spaced repetition (koncepty do powtórki)
- Daily goals
- Statystyki postępów per domain
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
from domain_manager import get_active_domain, list_domains


def generate_daily_goals(progress: dict, config: dict, active_domain: dict) -> list:
    """
    Generuj cele na dzisiaj (uniwersalne dla wszystkich dziedzin)

    Args:
        progress: Dict z postępem
        config: Dict z konfiguracją
        active_domain: Dict z aktywną domeną

    Returns:
        Lista string-ów z celami
    """
    session_num = progress.get("sessions", 0)
    domain_name = active_domain.get("name", "Your Domain") if active_domain else "Your Domain"

    goals = [
        "✍️ Pracuj nad zadaniami - praktyka czyni mistrza",
        "💡 Pytaj 'dlaczego' gdy coś jest niejasne",
        "🔗 Szukaj podobnych patternów w innych projektach"
    ]

    # Co 5 sesji - quiz reminder
    quiz_interval = config.get("daily_goals", {}).get("quiz_every_n_sessions", 5)
    if session_num > 0 and session_num % quiz_interval == 0:
        goals.insert(0, f"🎯 Dzisiaj: Test wiedzy z **{domain_name}** (/quiz)")

    return goals


def format_welcome_message(
    progress: dict,
    config: dict,
    to_review: list,
    learning_prompt: str,
    active_domain: dict,
    all_domains: list
) -> str:
    """
    Formatuj pełny welcome message (Universal Learning System v2.0)

    Args:
        progress: Dict z postępem
        config: Dict z konfiguracją
        to_review: Lista konceptów do powtórki
        learning_prompt: String z głównym promptem uczącym
        active_domain: Dict z aktywną domeną
        all_domains: Lista wszystkich dziedzin

    Returns:
        Sformatowany string z welcome message
    """
    session_num = progress.get("sessions", 0)
    streak = progress.get("streak_days", 0)
    streak_emoji = "🔥" if streak >= 3 else "⭐" if streak > 0 else "💤"

    # Active domain info
    domain_name = active_domain.get("name", "Universal Learning") if active_domain else "Universal Learning"
    domain_desc = active_domain.get("description", "") if active_domain else ""

    # Statystyki active domain
    domain_concepts = active_domain.get("concepts_count", 0) if active_domain else 0
    domain_mastered = active_domain.get("mastered_count", 0) if active_domain else 0

    # Statystyki globalne (wszystkie domeny)
    total_concepts = len(progress.get("concepts", {}))
    mastered_concepts = sum(
        1 for c in progress.get("concepts", {}).values()
        if c.get("mastery_level", 0) >= 3
    )

    # Daily goals
    goals = generate_daily_goals(progress, config, active_domain)
    goals_str = "\n".join(f"  {goal}" for goal in goals)

    # Concepts to review
    review_str = format_concepts_for_review(to_review)

    # Multi-domain section (if more than 1 domain)
    domains_section = ""
    if len(all_domains) > 1:
        domains_section = f"\n## 📚 Twoje Dziedziny ({len(all_domains)}):\n"
        for d in all_domains[:3]:  # Show max 3
            marker = "🎯" if d.get("id") == active_domain.get("id") else "  "
            name = d.get("name", "Unknown")
            progress_str = f"{d.get('mastered_count', 0)}/{d.get('concepts_count', 0)}"
            domains_section += f"{marker} **{name}** ({progress_str})\n"

        if len(all_domains) > 3:
            domains_section += f"\n_...i {len(all_domains) - 3} więcej. Użyj `/learn --list` aby zobaczyć wszystkie._\n"

    # Build message
    message = f"""
{learning_prompt}

---

# 🎓 SESJA UCZENIA #{session_num}

## 🎯 Aktywna Dziedzina: **{domain_name}**
_{domain_desc}_

**Progress:** {domain_mastered}/{domain_concepts} konceptów
{domains_section}
## Twoje Statystyki:
- {streak_emoji} **Passa:** {streak} dni pod rząd
- 📊 **Globalne koncepty:** {mastered_concepts}/{total_concepts} opanowane

## Dzisiejsze Cele:
{goals_str}

## Do Powtórki (Spaced Repetition):
{review_str}

---

**PAMIĘTAJ:** Tryb nauczania jest aktywny! Będę wyjaśniał, pozostawiał TODO(human) i pytał o zrozumienie.
Komendy: `/learn`, `/progress`, `/review`, `/concepts`, `/quiz`

Szczęśliwego kodowania! 🚀
"""

    return message.strip()


def main():
    """Główna funkcja SessionStart hook"""
    try:
        # Ensure data files exist
        ensure_data_files_exist()

        # Load config first to check if plugin is enabled
        config = load_config()

        # Check if plugin is enabled
        if not config.get("enabled", True):
            # Plugin is disabled - exit silently
            sys.exit(0)

        # Load data
        progress = load_progress()
        learning_prompt = load_learning_prompt()

        # Load domains (NEW - Universal Learning System v2.0)
        active_domain = get_active_domain()
        all_domains = list_domains()

        # Update session count and streak
        progress = update_session_count(progress)
        save_progress(progress)

        # Get concepts to review (if spaced repetition enabled)
        to_review = []
        if config.get("spaced_repetition", {}).get("enabled", True):
            to_review = get_concepts_to_review(progress, config)

        # Format welcome message
        message = format_welcome_message(
            progress, config, to_review, learning_prompt,
            active_domain, all_domains
        )

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
🎓 TRYB NAUCZANIA AKTYWNY - Universal Learning System v2.0

Będę Ci pomagał przez:
- 💡 Wyjaśnianie DLACZEGO coś działa (nie tylko JAK)
- ✍️ Zostawianie TODO(human) do samodzielnej implementacji
- 🔗 Pokazywanie powiązań między konceptami
- 🤔 Zadawanie pytań do refleksji

Dostępne komendy: `/learn`, `/progress`, `/review`, `/concepts`, `/quiz`

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
