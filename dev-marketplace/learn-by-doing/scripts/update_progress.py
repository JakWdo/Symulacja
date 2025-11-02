#!/usr/bin/env python3
"""
Update Progress - Główny orchestrator systemu uczenia się

Funkcjonalność:
- Skanuje practice log i wykrywa koncepty
- Aktualizuje learning_progress.json
- Oblicza category_progress
- Generuje rekomendacje
- Aktualizuje current_focus

Wywołanie:
- Automatycznie w SessionStart (jeśli enabled w config)
- Ręcznie przez komendę /track-concepts
"""
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import (
    load_progress,
    save_progress,
    load_config,
    load_knowledge_base,
    load_practice_log
)
from concept_detector import ConceptDetector
from learning_graph import LearningGraph
from recommendation_engine import RecommendationEngine


def update_progress(force_full_rescan: bool = False) -> Dict[str, Any]:
    """
    Główna funkcja - aktualizuj postęp uczenia się

    Args:
        force_full_rescan: Jeśli True, reskanuj cały practice log (nie tylko nowe)

    Returns:
        Dict z wynikami:
        {
            "success": True,
            "concepts_detected": 12,
            "concepts_updated": 5,
            "recommendations_generated": 3,
            "categories_updated": 6
        }
    """
    try:
        logger.info("=== Update Progress Started ===")

        # 1. Load data
        logger.info("Loading data...")
        progress = load_progress()
        config = load_config()
        kb = load_knowledge_base()
        practice_log = load_practice_log()

        if not kb.get("concepts"):
            logger.warning("Knowledge base jest pusty - skipping update")
            return {
                "success": False,
                "error": "Knowledge base is empty",
                "concepts_detected": 0,
                "concepts_updated": 0
            }

        if not practice_log:
            logger.warning("Practice log jest pusty - skipping update")
            return {
                "success": False,
                "error": "Practice log is empty",
                "concepts_detected": 0,
                "concepts_updated": 0
            }

        logger.info(f"  Loaded: {len(kb['concepts'])} concepts, {len(practice_log)} log entries")

        # 2. Detect concepts from practice log
        logger.info("Detecting concepts from practice log...")
        detector = ConceptDetector(kb)

        min_confidence = config.get("auto_tracking", {}).get("min_confidence", 0.7)
        detected_concepts = detector.detect_from_practice_log(
            practice_log,
            min_confidence=min_confidence
        )

        logger.info(f"  Detected {len(detected_concepts)} concepts")

        # 3. Update progress.concepts (merge z existing)
        logger.info("Updating progress.concepts...")
        updated_count = _merge_concepts(progress, detected_concepts)

        logger.info(f"  Updated {updated_count} concepts")

        # 4. Calculate category progress
        logger.info("Calculating category progress...")
        category_progress = detector.get_category_progress(progress["concepts"])
        progress["categories_progress"] = category_progress

        logger.info(f"  Updated {len(category_progress)} categories")

        # 5. Update current_focus (based on recent activity)
        logger.info("Updating current_focus...")
        current_focus = _calculate_current_focus(progress, practice_log, kb)
        progress["current_focus"] = current_focus

        logger.info(f"  Current focus: {current_focus.get('category', 'None')}")

        # 6. Generate recommendations
        logger.info("Generating recommendations...")
        if config.get("recommendations", {}).get("enabled", True):
            graph = LearningGraph(kb)
            engine = RecommendationEngine(kb, graph)

            max_suggestions = config.get("recommendations", {}).get("max_suggestions", 5)
            recommendations = engine.suggest_next_concepts(
                progress,
                config,
                max_suggestions=max_suggestions
            )

            progress["recommendations"] = {
                "generated_at": datetime.now().isoformat(),
                "next_steps": recommendations
            }

            logger.info(f"  Generated {len(recommendations)} recommendations")
        else:
            logger.info("  Recommendations disabled in config")
            recommendations = []

        # 7. Save progress
        logger.info("Saving progress...")
        if save_progress(progress):
            logger.info("✅ Progress saved successfully")
        else:
            logger.error("❌ Failed to save progress")
            return {
                "success": False,
                "error": "Failed to save progress"
            }

        logger.info("=== Update Progress Completed ===")

        return {
            "success": True,
            "concepts_detected": len(detected_concepts),
            "concepts_updated": updated_count,
            "recommendations_generated": len(recommendations),
            "categories_updated": len(category_progress)
        }

    except Exception as e:
        logger.exception(f"Error in update_progress: {e}")
        return {
            "success": False,
            "error": str(e),
            "concepts_detected": 0,
            "concepts_updated": 0
        }


def _merge_concepts(
    progress: Dict[str, Any],
    detected_concepts: Dict[str, Any]
) -> int:
    """
    Merge detected concepts z existing progress.concepts

    Args:
        progress: Dict z postępem (modyfikowany in-place)
        detected_concepts: Dict z wykrytymi konceptami

    Returns:
        Liczba zaktualizowanych konceptów
    """
    if "concepts" not in progress:
        progress["concepts"] = {}

    updated_count = 0

    for concept_id, detected_data in detected_concepts.items():
        existing = progress["concepts"].get(concept_id)

        if existing:
            # Update existing concept
            # Practice count - weź max (bo może być rescan)
            existing["practice_count"] = max(
                existing.get("practice_count", 0),
                detected_data["practice_count"]
            )

            # Last practiced - weź newest
            existing_last = existing.get("last_practiced", "")
            detected_last = detected_data.get("last_practiced", "")
            existing["last_practiced"] = max(existing_last, detected_last)

            # Mastery level - recalculate based on practice_count
            existing["mastery_level"] = detected_data["mastery_level"]

            # Confidence - average
            existing_conf = existing.get("confidence", detected_data["confidence"])
            existing["confidence"] = (existing_conf + detected_data["confidence"]) / 2

            # Evidence - append (keep max 10)
            existing_evidence = existing.get("evidence", [])
            new_evidence = detected_data.get("evidence", [])
            merged_evidence = existing_evidence + new_evidence
            existing["evidence"] = merged_evidence[-10:]  # Keep last 10

            # Unique files - merge
            existing_files = set(existing.get("unique_files", []))
            new_files = set(detected_data.get("unique_files", []))
            existing["unique_files"] = list(existing_files | new_files)[:5]

            # Next review
            existing["next_review"] = detected_data.get("next_review")

            updated_count += 1
        else:
            # New concept
            progress["concepts"][concept_id] = detected_data
            updated_count += 1

    return updated_count


def _calculate_current_focus(
    progress: Dict[str, Any],
    practice_log: List[Dict[str, Any]],
    knowledge_base: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Oblicz obecny focus na podstawie ostatnich aktywności

    Args:
        progress: Dict z postępem
        practice_log: Lista akcji
        knowledge_base: Dict z konceptami

    Returns:
        {
            "category": "Backend",
            "active_concepts": ["fastapi_async", "sqlalchemy_relationships"]
        }
    """
    # Weź ostatnie 20 akcji
    recent_logs = practice_log[-20:] if len(practice_log) > 20 else practice_log

    # Zbierz kategorie z recent concepts
    from collections import Counter
    category_counts = Counter()
    active_concepts_per_category = {}

    concepts = progress.get("concepts", {})
    kb_concepts = knowledge_base.get("concepts", {})

    for log_entry in reversed(recent_logs):
        # Find matching concepts (simple file-based matching)
        context = log_entry.get("context", {})
        file_path = context.get("file", "")

        if not file_path:
            continue

        # Sprawdź które koncepty pasują do tego pliku
        for concept_id, concept_data in concepts.items():
            if concept_id not in kb_concepts:
                continue

            kb_concept = kb_concepts[concept_id]
            category = kb_concept.get("category", "Other")

            # Check if file matches concept patterns (simplified)
            patterns = kb_concept.get("patterns", [])
            for pattern in patterns:
                if pattern.get("type") == "file":
                    path_pattern = pattern.get("path", "")
                    # Simplified matching
                    if any(part in file_path for part in path_pattern.replace("*", "").split("/")):
                        category_counts[category] += 1

                        if category not in active_concepts_per_category:
                            active_concepts_per_category[category] = set()
                        active_concepts_per_category[category].add(concept_id)
                        break

    # Most common category
    if not category_counts:
        return {
            "category": None,
            "active_concepts": []
        }

    most_common_category = category_counts.most_common(1)[0][0]
    active_concepts = list(active_concepts_per_category.get(most_common_category, set()))[:5]

    return {
        "category": most_common_category,
        "active_concepts": active_concepts
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Update learning progress")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full rescan of practice log"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode (no output)"
    )

    args = parser.parse_args()

    # Update progress
    result = update_progress(force_full_rescan=args.force)

    if not args.quiet:
        if result.get("success"):
            print(f"✅ Progress updated successfully")
            print(f"   Concepts detected: {result.get('concepts_detected', 0)}")
            print(f"   Concepts updated: {result.get('concepts_updated', 0)}")
            print(f"   Recommendations: {result.get('recommendations_generated', 0)}")
            print(f"   Categories: {result.get('categories_updated', 0)}")
        else:
            print(f"❌ Update failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
