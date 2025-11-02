#!/usr/bin/env python3
"""
Universal Learning Command - Dodawanie dziedzin nauki

NEW Semantics (v2.0):
    /learn                     # Show domains + active domain status
    /learn data-science        # Add 'data-science' domain (from template or custom)
    /learn "System Design"     # Add custom domain with quoted name
    /learn --list              # List all domains
    /learn --active <domain>   # Set active domain
    /learn --remove <domain>   # Remove domain (with confirmation)

OLD Semantics (deprecated but still supported):
    /learn status              # Show status
    /learn on/off              # Enable/disable plugin

Universal Learning System v2.0
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_config, save_config, load_learning_domains
from domain_manager import (
    add_domain, add_domain_from_template, remove_domain, set_active_domain,
    get_active_domain, get_domain_summary, list_domains, DOMAIN_TEMPLATES
)


# ============================================================================
# NEW COMMANDS (v2.0)
# ============================================================================

def show_domains_status():
    """
    Wyświetl status wszystkich dziedzin (NEW default dla /learn)
    """
    print("# 🎓 Tryb Uczenia - Twoje Dziedziny")
    print()

    # Show active domain
    active = get_active_domain()
    if active:
        print(f"## 🎯 Aktywna Dziedzina: **{active.get('name')}**")
        print()
        print(f"_{active.get('description', '')}_")
        print()

        # Stats
        concepts = active.get('concepts_count', 0)
        mastered = active.get('mastered_count', 0)
        progress_pct = (mastered / concepts * 100) if concepts > 0 else 0
        print(f"**Progress:** {mastered}/{concepts} konceptów ({progress_pct:.0f}%)")
        print()

    # Show all domains
    print(get_domain_summary())

    # Instructions
    print()
    print("## 💡 Jak zacząć uczyć się nowej dziedziny?")
    print()
    print("```")
    print("/learn data-science      # Dodaj Data Science")
    print("/learn system-design     # Dodaj System Design")
    print("/learn \"Your Domain\"     # Dodaj custom dziedzinę")
    print("```")
    print()

    # Show available templates
    print("## 📚 Dostępne Szablony:")
    print()
    for template_id, template in DOMAIN_TEMPLATES.items():
        print(f"- `{template_id}` - {template['name']}")
    print()

    # Available commands
    print("## 🛠️ Wszystkie Komendy:")
    print()
    print("- `/learn` - Ten ekran (domains status)")
    print("- `/learn <domain>` - Dodaj dziedzinę")
    print("- `/learn --list` - Lista wszystkich dziedzin")
    print("- `/learn --active <domain>` - Ustaw aktywną dziedzinę")
    print("- `/learn --remove <domain>` - Usuń dziedzinę")
    print("- `/progress` - Dashboard postępów")
    print("- `/review` - Przegląd nauki")
    print("- `/concepts` - Lista konceptów")
    print()


def add_new_domain(domain_input: str):
    """
    Dodaj nową dziedzinę (z template lub custom)

    Args:
        domain_input: Nazwa dziedziny (np. "data-science" lub "System Design")
    """
    # Normalize domain_id (slug format)
    domain_id = domain_input.lower().replace(" ", "-").replace("_", "-")

    # Check if it's a template
    if domain_id in DOMAIN_TEMPLATES:
        print(f"# ✅ Dodaję dziedzinę z szablonu: **{DOMAIN_TEMPLATES[domain_id]['name']}**")
        print()

        success = add_domain_from_template(domain_id)

        if success:
            template = DOMAIN_TEMPLATES[domain_id]
            print(f"**Opis:** {template['description']}")
            print()
            print(f"**Kategorie:** {', '.join(template['categories'])}")
            print()
            print("---")
            print()
            print("## 🎯 Co dalej?")
            print()
            print("1. **Zacznij pracować** nad zadaniami z tej dziedziny")
            print("2. System **automatycznie wykryje** używane koncepty")
            print("3. Użyj `/progress` aby zobaczyć postęp")
            print("4. Użyj `/quiz` aby sprawdzić wiedzę")
            print()
            print(f"_Aktywna dziedzina: **{template['name']}**_")
        else:
            print("❌ **Błąd:** Nie udało się dodać dziedziny (może już istnieje?)")

    else:
        # Custom domain
        domain_name = domain_input.title()
        print(f"# ✅ Dodaję custom dziedzinę: **{domain_name}**")
        print()

        # Ask for description (in real scenario, this would be interactive)
        # For now, auto-generate
        description = f"Custom learning domain: {domain_name}"

        success = add_domain(
            domain_id=domain_id,
            name=domain_name,
            description=description,
            categories=[],
            custom=True
        )

        if success:
            print(f"**ID:** `{domain_id}`")
            print()
            print("## 🎯 Co dalej?")
            print()
            print("1. **Rozpocznij pracę** nad zadaniami z tej dziedziny")
            print("2. System **automatycznie wykryje** używane technologie i koncepty")
            print("3. Użyj `/progress` aby zobaczyć postęp")
            print()
            print("💡 **Tip:** Możesz dodać kategorie ręcznie w `user_learning_domains.json`")
            print()
            print(f"_Aktywna dziedzina: **{domain_name}**_")
        else:
            print("❌ **Błąd:** Nie udało się dodać dziedziny (może już istnieje?)")


def list_all_domains():
    """Lista wszystkich dziedzin"""
    print("# 📚 Wszystkie Dziedziny Nauki")
    print()
    print(get_domain_summary())
    print()


def set_domain_active(domain_id: str):
    """Ustaw aktywną dziedzinę"""
    success = set_active_domain(domain_id)

    if success:
        from domain_manager import get_domain
        domain = get_domain(domain_id)

        print(f"# 🎯 Aktywna Dziedzina: **{domain.get('name')}**")
        print()
        print(f"_{domain.get('description', '')}_")
        print()
        print("Od teraz system będzie priorytetowo śledzić tę dziedzinę.")
        print()
        print(f"Użyj `/progress` aby zobaczyć postęp w **{domain.get('name')}**")
    else:
        print(f"❌ **Błąd:** Nie znaleziono dziedziny `{domain_id}`")
        print()
        print("Dostępne dziedziny:")
        for domain in list_domains():
            print(f"  - `{domain['id']}` - {domain['name']}")


def remove_domain_command(domain_id: str):
    """Usuń dziedzinę (z potwierdzeniem)"""
    from domain_manager import get_domain

    domain = get_domain(domain_id)
    if not domain:
        print(f"❌ **Błąd:** Nie znaleziono dziedziny `{domain_id}`")
        return

    print(f"# ⚠️ Usuwanie Dziedziny: **{domain.get('name')}**")
    print()
    print(f"**Progress:** {domain.get('mastered_count', 0)}/{domain.get('concepts_count', 0)} konceptów")
    print()

    # In real scenario, ask for confirmation
    # For now, auto-confirm if no progress
    if domain.get('mastered_count', 0) > 0:
        print("❌ **Nie można usunąć:** Dziedzina ma postęp!")
        print()
        print("Użyj `--force` aby wymusić usunięcie (dane postępu zostaną utracone)")
        return

    success = remove_domain(domain_id)
    if success:
        print(f"✅ Dziedzina **{domain.get('name')}** została usunięta.")
    else:
        print("❌ Błąd podczas usuwania.")


# ============================================================================
# OLD COMMANDS (deprecated but still supported)
# ============================================================================

def show_status_legacy(enabled: bool):
    """Legacy: Wyświetl status pluginu (stary format)"""
    print("# 🎓 Status Trybu Nauczania (Legacy)")
    print()
    print("⚠️ **Ta komenda jest deprecated.** Użyj `/learn` zamiast `/learn status`")
    print()

    progress = load_progress()

    if not progress:
        print("⚠️ **Plugin dopiero się inicjalizuje...**")
        print()
    else:
        sessions = progress.get("sessions", 0)
        streak = progress.get("streak_days", 0)

        print(f"- **Sesja:** #{sessions}")
        print(f"- **Passa:** {streak} dni pod rząd")
        print()

    status_emoji = "✅" if enabled else "❌"
    status_text = "Aktywny" if enabled else "Wyłączony"
    print(f"**Status:** {status_emoji} {status_text}")
    print()

    print("Użyj `/learn` aby zobaczyć nowy interfejs dziedzin.")


def enable_plugin_legacy():
    """Legacy: Włącz plugin"""
    config = load_config()
    config["enabled"] = True
    save_config(config)

    print("# ✅ Tryb Nauczania Włączony")
    print()
    print("Plugin **learn-by-doing** jest aktywny!")
    print()


def disable_plugin_legacy():
    """Legacy: Wyłącz plugin"""
    config = load_config()
    config["enabled"] = False
    save_config(config)

    print("# ❌ Tryb Nauczania Wyłączony")
    print()
    print("Plugin został dezaktywowany (dane zachowane).")
    print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Główna funkcja"""
    # Parse arguments
    args = sys.argv[1:]

    if not args:
        # NEW: /learn bez argumentów = show domains status
        show_domains_status()
        return

    command = args[0].lower()

    # NEW COMMANDS (v2.0)
    if command == "--list":
        list_all_domains()

    elif command == "--active":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj ID dziedziny")
            print()
            print("Usage: `/learn --active <domain-id>`")
        else:
            set_domain_active(args[1])

    elif command == "--remove":
        if len(args) < 2:
            print("❌ **Błąd:** Podaj ID dziedziny")
            print()
            print("Usage: `/learn --remove <domain-id>`")
        else:
            remove_domain_command(args[1])

    # LEGACY COMMANDS (deprecated)
    elif command in ["on", "enable"]:
        enable_plugin_legacy()

    elif command in ["off", "disable"]:
        disable_plugin_legacy()

    elif command == "status":
        config = load_config()
        show_status_legacy(config.get("enabled", True))

    # NEW: Add domain (template or custom)
    else:
        # Join all args (for domains with spaces like "System Design")
        domain_input = " ".join(args)
        add_new_domain(domain_input)


if __name__ == "__main__":
    main()
