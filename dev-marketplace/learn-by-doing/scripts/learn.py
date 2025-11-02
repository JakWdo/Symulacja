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
    if active:
        domain_icon = active.get('icon', '📚')
        domain_name = active.get('name', '')
        print(f"{domain_icon} **Dziedzina:** {domain_name}")
        print()

    print("🤖 **Claude generuje plan kursu...**")
    print()
    print("_(To wymaga interakcji z course_planner.py - zostanie zaimplementowane)_")
    print()
    print("💡 **Tymczasowo:** Użyj normalnej konwersacji z Claude:")
    print(f'   "Chcę nauczyć się: {goal}"')
    print()


def continue_last_course():
    """
    Kontynuuj ostatni aktywny kurs
    """
    print("# 📖 Kontynuuj Naukę")
    print()
    print("_(Funkcja zostanie zaimplementowana po integracji z course_manager)_")
    print()
    print("💡 **Tymczasowo:** Zapytaj Claude:")
    print('   "Kontynuujmy ostatnią lekcję"')
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

    elif command == "continue":
        continue_last_course()

    else:
        # Main: start new course
        goal = " ".join(args)
        start_course_planning(goal)


if __name__ == "__main__":
    main()
