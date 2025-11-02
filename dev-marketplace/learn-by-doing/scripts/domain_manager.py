#!/usr/bin/env python3
"""
Domain Manager - CRUD operations for learning domains

Odpowiedzialności:
- Dodawanie nowych dziedzin (data science, math, physics, etc.)
- Usuwanie dziedzin
- Aktualizacja statystyk dziedzin
- Ustawianie aktywnej dziedziny
- Pobieranie informacji o dziedzinach

Universal Learning System v2.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import data_manager
import sys
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_learning_domains, save_learning_domains

logger = logging.getLogger(__name__)


# ============================================================================
# DOMAIN CRUD OPERATIONS
# ============================================================================

def add_domain(
    domain_id: str,
    name: str,
    description: str = "",
    categories: Optional[List[str]] = None,
    custom: bool = True
) -> bool:
    """
    Dodaj nową dziedzinę nauki

    Args:
        domain_id: Unikalny ID dziedziny (slug format: "data-science", "system-design")
        name: Nazwa wyświetlana (np. "Data Science", "System Design")
        description: Opis dziedziny
        categories: Lista kategorii (np. ["pandas", "numpy", "ML"])
        custom: Czy to custom domain (True) czy predefiniowany (False)

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        domains_data = load_learning_domains()

        # Sprawdź czy domain już istnieje
        if domain_id in domains_data.get("domains", {}):
            logger.warning(f"Domain '{domain_id}' already exists")
            return False

        # Dodaj nowy domain
        domains_data["domains"][domain_id] = {
            "name": name,
            "description": description,
            "added_at": datetime.now().isoformat(),
            "active": True,
            "categories": categories or [],
            "concepts_count": 0,
            "mastered_count": 0,
            "last_practice": None,
            "custom": custom
        }

        # Jeśli to pierwszy custom domain, ustaw jako aktywny
        if custom and domains_data.get("active_domain") is None:
            domains_data["active_domain"] = domain_id

        success = save_learning_domains(domains_data)
        if success:
            logger.info(f"✅ Added domain: {name} ({domain_id})")
        return success

    except Exception as e:
        logger.error(f"Error adding domain: {e}")
        return False


def remove_domain(domain_id: str, force: bool = False) -> bool:
    """
    Usuń dziedzinę nauki

    Args:
        domain_id: ID dziedziny do usunięcia
        force: Jeśli True, usuń nawet jeśli ma progress (default: False)

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        domains_data = load_learning_domains()

        if domain_id not in domains_data.get("domains", {}):
            logger.warning(f"Domain '{domain_id}' not found")
            return False

        domain = domains_data["domains"][domain_id]

        # Sprawdź czy ma progress
        if not force and domain.get("mastered_count", 0) > 0:
            logger.warning(f"Domain '{domain_id}' has progress. Use force=True to remove")
            return False

        # Usuń domain
        del domains_data["domains"][domain_id]

        # Jeśli to był aktywny domain, wybierz inny
        if domains_data.get("active_domain") == domain_id:
            remaining_domains = list(domains_data["domains"].keys())
            domains_data["active_domain"] = remaining_domains[0] if remaining_domains else None

        success = save_learning_domains(domains_data)
        if success:
            logger.info(f"❌ Removed domain: {domain_id}")
        return success

    except Exception as e:
        logger.error(f"Error removing domain: {e}")
        return False


def set_active_domain(domain_id: str) -> bool:
    """
    Ustaw aktywną dziedzinę nauki

    Args:
        domain_id: ID dziedziny

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        domains_data = load_learning_domains()

        if domain_id not in domains_data.get("domains", {}):
            logger.warning(f"Domain '{domain_id}' not found")
            return False

        domains_data["active_domain"] = domain_id

        success = save_learning_domains(domains_data)
        if success:
            logger.info(f"🎯 Active domain set to: {domain_id}")
        return success

    except Exception as e:
        logger.error(f"Error setting active domain: {e}")
        return False


def get_domain(domain_id: str) -> Optional[Dict[str, Any]]:
    """
    Pobierz informacje o dziedzinie

    Args:
        domain_id: ID dziedziny

    Returns:
        Dict z danymi dziedziny lub None jeśli nie znaleziono
    """
    try:
        domains_data = load_learning_domains()
        return domains_data.get("domains", {}).get(domain_id)

    except Exception as e:
        logger.error(f"Error getting domain: {e}")
        return None


def get_active_domain() -> Optional[Dict[str, Any]]:
    """
    Pobierz aktywną dziedzinę

    Returns:
        Dict z danymi aktywnej dziedziny lub None
    """
    try:
        domains_data = load_learning_domains()
        active_id = domains_data.get("active_domain")

        if active_id is None:
            return None

        domain = domains_data.get("domains", {}).get(active_id)
        if domain:
            domain["id"] = active_id  # Dodaj ID doDict
        return domain

    except Exception as e:
        logger.error(f"Error getting active domain: {e}")
        return None


def list_domains(active_only: bool = False) -> List[Dict[str, Any]]:
    """
    Pobierz listę wszystkich dziedzin

    Args:
        active_only: Jeśli True, zwróć tylko aktywne dziedziny

    Returns:
        Lista Dict-ów z danymi dziedzin
    """
    try:
        domains_data = load_learning_domains()
        domains = []

        for domain_id, domain_data in domains_data.get("domains", {}).items():
            if active_only and not domain_data.get("active", True):
                continue

            domain_dict = {**domain_data, "id": domain_id}
            domains.append(domain_dict)

        # Sort by added_at (newest first)
        domains.sort(key=lambda x: x.get("added_at", ""), reverse=True)

        return domains

    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        return []


def update_domain_stats(
    domain_id: str,
    concepts_count: Optional[int] = None,
    mastered_count: Optional[int] = None,
    last_practice: Optional[str] = None
) -> bool:
    """
    Aktualizuj statystyki dziedziny

    Args:
        domain_id: ID dziedziny
        concepts_count: Liczba wszystkich konceptów (opcjonalne)
        mastered_count: Liczba opanowanych konceptów (opcjonalne)
        last_practice: ISO timestamp ostatniej praktyki (opcjonalne)

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        domains_data = load_learning_domains()

        if domain_id not in domains_data.get("domains", {}):
            logger.warning(f"Domain '{domain_id}' not found")
            return False

        domain = domains_data["domains"][domain_id]

        # Update stats
        if concepts_count is not None:
            domain["concepts_count"] = concepts_count
        if mastered_count is not None:
            domain["mastered_count"] = mastered_count
        if last_practice is not None:
            domain["last_practice"] = last_practice
        elif concepts_count is not None or mastered_count is not None:
            # Auto-update last_practice when stats change
            domain["last_practice"] = datetime.now().isoformat()

        success = save_learning_domains(domains_data)
        return success

    except Exception as e:
        logger.error(f"Error updating domain stats: {e}")
        return False


def toggle_domain_active(domain_id: str) -> bool:
    """
    Przełącz stan aktywności dziedziny (on/off)

    Args:
        domain_id: ID dziedziny

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    try:
        domains_data = load_learning_domains()

        if domain_id not in domains_data.get("domains", {}):
            logger.warning(f"Domain '{domain_id}' not found")
            return False

        domain = domains_data["domains"][domain_id]
        domain["active"] = not domain.get("active", True)

        success = save_learning_domains(domains_data)
        if success:
            state = "activated" if domain["active"] else "deactivated"
            logger.info(f"Domain '{domain_id}' {state}")
        return success

    except Exception as e:
        logger.error(f"Error toggling domain active: {e}")
        return False


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_domain_summary(domain: Dict[str, Any]) -> str:
    """
    Formatuj podsumowanie dziedziny do wyświetlenia

    Args:
        domain: Dict z danymi dziedziny

    Returns:
        Sformatowany string
    """
    name = domain.get("name", "Unknown")
    desc = domain.get("description", "")
    concepts = domain.get("concepts_count", 0)
    mastered = domain.get("mastered_count", 0)
    last = domain.get("last_practice")
    active = "🟢" if domain.get("active", True) else "🔴"

    lines = [f"{active} **{name}**"]
    if desc:
        lines.append(f"  {desc}")
    lines.append(f"  Progress: {mastered}/{concepts} konceptów")

    if last:
        try:
            last_date = datetime.fromisoformat(last)
            days_ago = (datetime.now() - last_date).days
            if days_ago == 0:
                last_str = "dzisiaj"
            elif days_ago == 1:
                last_str = "wczoraj"
            else:
                last_str = f"{days_ago} dni temu"
            lines.append(f"  Ostatnia praktyka: {last_str}")
        except ValueError:
            pass

    return "\n".join(lines)


def get_domain_summary() -> str:
    """
    Pobierz podsumowanie wszystkich dziedzin

    Returns:
        Sformatowany string z listą dziedzin
    """
    domains = list_domains()

    if not domains:
        return "Brak dziedzin. Dodaj pierwszą używając: /learn <nazwa-dziedziny>"

    active_domain_data = get_active_domain()
    active_id = active_domain_data.get("id") if active_domain_data else None

    lines = ["📚 **Twoje Dziedziny Nauki:**\n"]

    for domain in domains:
        domain_id = domain.get("id")
        is_active = (domain_id == active_id)
        marker = "➡️  " if is_active else "    "

        summary = format_domain_summary(domain)
        lines.append(marker + summary.replace("\n", "\n" + marker) + "\n")

    return "\n".join(lines)


# ============================================================================
# DOMAIN TEMPLATES
# ============================================================================

DOMAIN_TEMPLATES = {
    "data-science": {
        "name": "Data Science",
        "description": "Analiza danych, wizualizacja, machine learning",
        "categories": ["pandas", "numpy", "matplotlib", "sklearn", "stats"],
    },
    "system-design": {
        "name": "System Design",
        "description": "Projektowanie skalowalnych systemów",
        "categories": ["scalability", "databases", "caching", "load-balancing", "microservices"],
    },
    "mathematics": {
        "name": "Mathematics",
        "description": "Matematyka dla programistów i data science",
        "categories": ["linear-algebra", "calculus", "statistics", "probability", "optimization"],
    },
    "machine-learning": {
        "name": "Machine Learning",
        "description": "Uczenie maszynowe i deep learning",
        "categories": ["supervised", "unsupervised", "deep-learning", "neural-networks", "transformers"],
    },
    "algorithms": {
        "name": "Algorithms & Data Structures",
        "description": "Algorytmy i struktury danych",
        "categories": ["sorting", "searching", "graphs", "trees", "dynamic-programming"],
    },
}


def add_domain_from_template(template_id: str) -> bool:
    """
    Dodaj dziedzinę z gotowego szablonu

    Args:
        template_id: ID szablonu (np. "data-science", "system-design")

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    if template_id not in DOMAIN_TEMPLATES:
        logger.warning(f"Template '{template_id}' not found")
        return False

    template = DOMAIN_TEMPLATES[template_id]
    return add_domain(
        domain_id=template_id,
        name=template["name"],
        description=template["description"],
        categories=template["categories"],
        custom=True
    )


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test domain manager functions"""
    print("Testing domain_manager.py...\n")

    # List existing domains
    print("=== Existing Domains ===")
    print(get_domain_summary())

    # Add new domain from template
    print("\n=== Adding 'data-science' domain ===")
    success = add_domain_from_template("data-science")
    print(f"Result: {success}")

    # List domains again
    print("\n=== Updated Domains ===")
    print(get_domain_summary())

    # Set active domain
    print("\n=== Setting 'data-science' as active ===")
    set_active_domain("data-science")

    # Get active domain
    active = get_active_domain()
    print(f"Active domain: {active.get('name') if active else 'None'}")

    print("\n✅ Tests completed!")
