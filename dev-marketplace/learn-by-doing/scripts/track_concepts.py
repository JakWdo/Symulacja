#!/usr/bin/env python3
"""
Track Concepts Command - Ręczne wywołanie update progress

Użycie:
  /track-concepts              # Normal update
  /track-concepts --force      # Force full rescan
"""
import sys
from pathlib import Path

# Import update_progress
sys.path.insert(0, str(Path(__file__).parent))
from update_progress import update_progress


def main():
    """Main entry point for /track-concepts command"""
    # Check for --force flag
    force = "--force" in sys.argv

    print("🔍 Skanowanie practice log i aktualizacja konceptów...")

    if force:
        print("   (Full rescan mode)")

    # Run update
    result = update_progress(force_full_rescan=force)

    # Display results
    if result.get("success"):
        print("\n✅ Koncepty zaktualizowane!")
        print(f"   📊 Wykryte: {result.get('concepts_detected', 0)} konceptów")
        print(f"   🔄 Zaktualizowane: {result.get('concepts_updated', 0)} konceptów")
        print(f"   💡 Rekomendacje: {result.get('recommendations_generated', 0)} sugestii")
        print(f"   📂 Kategorie: {result.get('categories_updated', 0)} kategorii")
        print("\nUżyj /learn aby zobaczyć szczegóły")
    else:
        error = result.get("error", "Unknown error")
        print(f"\n❌ Błąd podczas aktualizacji: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
