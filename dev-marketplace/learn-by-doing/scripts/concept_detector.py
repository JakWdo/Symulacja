#!/usr/bin/env python3
"""
Concept Detector - Automatyczne wykrywanie używanych konceptów z practice log

Funkcjonalność:
- Pattern matching (regex na kod, ścieżki plików, bash commands)
- Confidence scoring
- Practice counting
- Evidence collection (pliki + linijki kodu)
"""
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConceptDetector:
    """
    Wykrywa koncepty na podstawie practice log i knowledge base
    """

    def __init__(self, knowledge_base: Dict[str, Any]):
        """
        Args:
            knowledge_base: Dict z konceptami i patterns
        """
        self.knowledge_base = knowledge_base
        self.concepts = knowledge_base.get("concepts", {})

    def detect_from_practice_log(
        self,
        log_entries: List[Dict[str, Any]],
        min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Analizuje practice log i wykrywa wszystkie używane koncepty

        Args:
            log_entries: Lista dict-ów z practice_log.jsonl
            min_confidence: Minimalny poziom pewności (0.0 - 1.0)

        Returns:
            Dict z wykrytymi konceptami:
            {
                "concept_id": {
                    "name": "Concept Name",
                    "category": "Backend",
                    "detected": True,
                    "confidence": 0.95,
                    "practice_count": 5,
                    "evidence": [
                        {"file": "app/api/projects.py", "timestamp": "...", "action": "file_edit"},
                        ...
                    ],
                    "first_practiced": "2025-10-15T...",
                    "last_practiced": "2025-11-02T...",
                    "mastery_level": 1  # będzie obliczane później
                },
                ...
            }
        """
        detected_concepts = {}

        # Zbierz wszystkie dopasowania dla każdego konceptu
        concept_matches = defaultdict(list)

        for log_entry in log_entries:
            matches = self.detect_from_log_entry(log_entry)

            for concept_id, match_data in matches.items():
                concept_matches[concept_id].append({
                    "timestamp": log_entry.get("timestamp"),
                    "file": match_data.get("file"),
                    "action": log_entry.get("action"),
                    "confidence": match_data.get("confidence", 1.0)
                })

        # Przetwórz każdy koncept
        for concept_id, matches in concept_matches.items():
            if concept_id not in self.concepts:
                continue

            concept_def = self.concepts[concept_id]

            # Oblicz overall confidence (średnia z wszystkich match-ów)
            avg_confidence = sum(m["confidence"] for m in matches) / len(matches)

            if avg_confidence < min_confidence:
                continue

            # Sortuj matches po timestamp
            matches.sort(key=lambda x: x.get("timestamp", ""))

            # Zlicz praktyki (unikalne pliki)
            unique_files = set(m["file"] for m in matches if m.get("file"))
            practice_count = len(matches)

            # Pierwsze i ostatnie użycie
            first_practiced = matches[0]["timestamp"] if matches else None
            last_practiced = matches[-1]["timestamp"] if matches else None

            # Oblicz mastery level na podstawie practice_count
            mastery_level = self.calculate_mastery_level(practice_count)

            detected_concepts[concept_id] = {
                "name": concept_def["name"],
                "category": concept_def["category"],
                "subcategory": concept_def.get("subcategory", ""),
                "detected": True,
                "confidence": round(avg_confidence, 2),
                "practice_count": practice_count,
                "evidence": matches[:10],  # Max 10 najnowszych
                "unique_files": list(unique_files)[:5],  # Max 5 plików
                "first_practiced": first_practiced,
                "last_practiced": last_practiced,
                "mastery_level": mastery_level,
                "next_review": self.calculate_next_review(last_practiced, mastery_level)
            }

        return detected_concepts

    def detect_from_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Wykryj koncepty z pojedynczego entry w practice log

        Args:
            log_entry: Dict z akcją (timestamp, action, context, etc.)

        Returns:
            Dict z dopasowanymi konceptami: {concept_id: {file, confidence}}
        """
        matches = {}

        action = log_entry.get("action", "")
        context = log_entry.get("context", {})
        file_path = context.get("file", "")

        # Dla każdego konceptu sprawdź patterns
        for concept_id, concept_def in self.concepts.items():
            patterns = concept_def.get("patterns", [])

            match_score = 0.0
            match_count = 0

            for pattern in patterns:
                pattern_type = pattern.get("type")

                if pattern_type == "file" and file_path:
                    # File path matching
                    path_pattern = pattern.get("path", "")
                    if self.match_file_path(file_path, path_pattern):
                        match_score += 1.0
                        match_count += 1

                elif pattern_type == "bash" and action == "bash_command":
                    # Bash command matching
                    # TODO: W przyszłości będzie context.bash_command
                    pass

                elif pattern_type == "code":
                    # Code regex matching
                    # TODO: W przyszłości będzie context.code_snippet
                    # Na razie używamy file path jako proxy
                    if file_path:
                        match_score += 0.5
                        match_count += 1

            if match_count > 0:
                confidence = match_score / max(len(patterns), 1)
                matches[concept_id] = {
                    "file": file_path,
                    "confidence": confidence
                }

        return matches

    def match_file_path(self, file_path: str, pattern: str) -> bool:
        """
        Dopasuj ścieżkę pliku do patternu (glob-like)

        Args:
            file_path: Ścieżka pliku (np. "app/api/projects.py")
            pattern: Pattern (np. "app/api/*.py", "**/*.tsx")

        Returns:
            True jeśli pasuje
        """
        # Convert glob pattern to regex
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"

        try:
            return bool(re.match(regex_pattern, file_path))
        except re.error:
            logger.warning(f"Invalid regex pattern: {regex_pattern}")
            return False

    def match_code_regex(self, code: str, pattern: str) -> bool:
        """
        Dopasuj kod do regex patternu

        Args:
            code: Fragment kodu
            pattern: Regex pattern

        Returns:
            True jeśli pasuje
        """
        try:
            return bool(re.search(pattern, code))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False

    def calculate_mastery_level(self, practice_count: int) -> int:
        """
        Oblicz mastery level na podstawie liczby praktyk

        Args:
            practice_count: Liczba użyć konceptu

        Returns:
            1-5 (Beginner → Expert)
        """
        if practice_count < 4:
            return 1  # Beginner
        elif practice_count < 9:
            return 2  # Intermediate
        elif practice_count < 16:
            return 3  # Proficient
        elif practice_count < 30:
            return 4  # Advanced
        else:
            return 5  # Expert

    def calculate_next_review(self, last_practiced: Optional[str], mastery_level: int) -> Optional[str]:
        """
        Oblicz datę następnej powtórki (spaced repetition)

        Args:
            last_practiced: ISO datetime string
            mastery_level: 1-5

        Returns:
            ISO datetime string następnej powtórki
        """
        if not last_practiced:
            return None

        try:
            last_date = datetime.fromisoformat(last_practiced)
        except ValueError:
            return None

        # Intervals: [1, 3, 7, 14, 30] dni
        intervals = [1, 3, 7, 14, 30]
        days = intervals[min(mastery_level - 1, len(intervals) - 1)]

        from datetime import timedelta
        next_review_date = last_date + timedelta(days=days)

        return next_review_date.isoformat()

    def auto_discover_new_concepts(self, log_entries: List[Dict[str, Any]]) -> List[str]:
        """
        Wykryj używane technologie które NIE są w knowledge base

        Args:
            log_entries: Lista dict-ów z practice_log.jsonl

        Returns:
            Lista nazw nieznanych technologii (np. ["pytest-cov", "black", "ruff"])
        """
        # TODO: Advanced feature - wykrywanie nowych technologii
        # Można by analizować imports, bash commands, package.json, requirements.txt
        return []

    def get_category_progress(self, detected_concepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Oblicz postęp w każdej kategorii

        Args:
            detected_concepts: Dict z wykrytymi konceptami

        Returns:
            Dict z postępem per kategoria:
            {
                "Backend": {
                    "total_concepts": 12,
                    "detected": 5,
                    "mastered": 2,  # mastery_level >= 3
                    "in_progress": 3,  # mastery_level 1-2
                    "progress": 0.42  # mastered / total
                },
                ...
            }
        """
        # Zlicz wszystkie koncepty per kategoria (z knowledge base)
        total_per_category = defaultdict(int)
        for concept_def in self.concepts.values():
            category = concept_def.get("category", "Other")
            total_per_category[category] += 1

        # Zlicz wykryte i opanowane
        category_progress = {}

        for category in total_per_category.keys():
            detected = [
                c for c in detected_concepts.values()
                if c.get("category") == category
            ]

            mastered = [c for c in detected if c.get("mastery_level", 0) >= 3]
            in_progress = [c for c in detected if c.get("mastery_level", 0) < 3]

            total = total_per_category[category]
            progress = len(mastered) / total if total > 0 else 0.0

            category_progress[category] = {
                "total_concepts": total,
                "detected": len(detected),
                "mastered": len(mastered),
                "in_progress": len(in_progress),
                "progress": round(progress, 2)
            }

        return category_progress


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test concept detector"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from data_manager import load_knowledge_base, load_practice_log

    print("Testing concept_detector.py...")

    # Load data
    kb = load_knowledge_base()
    logs = load_practice_log()

    if not kb.get("concepts"):
        print("❌ Knowledge base jest pusty")
        sys.exit(1)

    print(f"\n✅ Loaded {len(kb['concepts'])} concepts from knowledge base")
    print(f"✅ Loaded {len(logs)} log entries")

    # Detect concepts
    detector = ConceptDetector(kb)
    detected = detector.detect_from_practice_log(logs, min_confidence=0.5)

    print(f"\n🔍 Detected {len(detected)} concepts:")
    for concept_id, data in list(detected.items())[:10]:
        print(f"  • {data['name']} ({data['category']}) - {data['practice_count']} uses, confidence={data['confidence']}")

    # Category progress
    cat_progress = detector.get_category_progress(detected)
    print(f"\n📊 Category Progress:")
    for cat, prog in cat_progress.items():
        if prog['detected'] > 0:
            print(f"  • {cat}: {prog['mastered']}/{prog['total_concepts']} mastered ({prog['progress']*100:.0f}%)")
