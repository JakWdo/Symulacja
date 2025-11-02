#!/usr/bin/env python3
"""
Lista wszystkich konceptów (static + dynamic)

Użycie:
  /concepts                    # Wszystkie koncepty
  /concepts --category Backend # Filtruj po kategorii
  /concepts --discovered       # Tylko auto-discovered
  /concepts --mastered         # Tylko opanowane (mastery >= 3)
"""
import sys
from pathlib import Path
from collections import defaultdict

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_progress, load_knowledge_base, load_dynamic_concepts
from concept_manager import ConceptManager


def format_mastery_icon(mastery_level):
    """Format mastery level as emoji"""
    if mastery_level >= 4:
        return "✅"
    elif mastery_level >= 2:
        return "🔄"
    else:
        return "⏳"


def main():
    """Main entry point for /concepts command"""
    # Parse arguments
    args = sys.argv[1:]
    filter_category = None
    show_discovered_only = False
    show_mastered_only = False

    for i, arg in enumerate(args):
        if arg == "--category" and i + 1 < len(args):
            filter_category = args[i + 1]
        elif arg == "--discovered":
            show_discovered_only = True
        elif arg == "--mastered":
            show_mastered_only = True

    # Load data
    kb = load_knowledge_base()
    dynamic = load_dynamic_concepts()
    progress = load_progress()

    manager = ConceptManager(kb, dynamic)
    all_concepts = manager.get_all_concepts()
    user_concepts = progress.get("concepts", {})

    # Filter concepts
    filtered_concepts = {}

    for concept_id, concept_def in all_concepts.items():
        # Filter by category
        if filter_category and concept_def.get("category") != filter_category:
            continue

        # Filter by discovered
        if show_discovered_only and not concept_def.get("auto_discovered"):
            continue

        # Filter by mastered
        if show_mastered_only:
            user_data = user_concepts.get(concept_id, {})
            if user_data.get("mastery_level", 0) < 3:
                continue

        filtered_concepts[concept_id] = concept_def

    # Group by category
    by_category = defaultdict(list)
    for concept_id, concept_def in filtered_concepts.items():
        category = concept_def.get("category", "Other")
        user_data = user_concepts.get(concept_id, {})

        by_category[category].append({
            "id": concept_id,
            "name": concept_def["name"],
            "mastery_level": user_data.get("mastery_level", 0),
            "practice_count": user_data.get("practice_count", 0),
            "auto_discovered": concept_def.get("auto_discovered", False)
        })

    # Print header
    print("# 📚 TWOJE KONCEPTY")
    print()

    total_concepts = len(filtered_concepts)
    mastered_count = sum(
        1 for c in user_concepts.values()
        if c.get("mastery_level", 0) >= 3
    )
    discovered_count = len(dynamic)

    print(f"**Total:** {total_concepts} konceptów | **Opanowane:** {mastered_count} | **Auto-discovered:** {discovered_count}")
    print()

    if not filtered_concepts:
        print("_Brak konceptów spełniających kryteria._")
        print()
        print("**Dostępne filtry:**")
        print("- `/concepts --category Backend` - Filtruj po kategorii")
        print("- `/concepts --discovered` - Tylko auto-discovered")
        print("- `/concepts --mastered` - Tylko opanowane (mastery >= 3)")
        return

    # Print concepts by category
    for category in sorted(by_category.keys()):
        concepts = by_category[category]

        print(f"## {category} ({len(concepts)} concepts)")
        print()

        # Sort by mastery level (descending), then by practice count
        concepts.sort(key=lambda x: (-x["mastery_level"], -x["practice_count"]))

        for concept in concepts:
            icon = format_mastery_icon(concept["mastery_level"])
            name = concept["name"]
            mastery = concept["mastery_level"]
            uses = concept["practice_count"]

            # Auto-discovered marker
            auto_marker = " ⭐" if concept["auto_discovered"] else ""

            if mastery > 0:
                print(f"  {icon} **{name}** (mastery {mastery}) - {uses} uses{auto_marker}")
            else:
                print(f"  ⚪ {name} - Not practiced yet{auto_marker}")

        print()

    # Footer
    print("---")
    print()
    print("**Legenda:**")
    print("- ✅ = Opanowane (mastery 4-5)")
    print("- 🔄 = W trakcie (mastery 2-3)")
    print("- ⏳ = Początkujący (mastery 1)")
    print("- ⚪ = Nie praktykowane")
    print("- ⭐ = Auto-discovered")
    print()
    print("**Użyj:** `/learn` aby zobaczyć szczegóły konceptu")


if __name__ == "__main__":
    main()
