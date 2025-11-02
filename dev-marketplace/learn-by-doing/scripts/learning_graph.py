#!/usr/bin/env python3
"""
Learning Graph - Dependency graph konceptów i pathfinding

Funkcjonalność:
- Graf zależności (prerequisites → concept → next_steps)
- Znajdowanie dostępnych next steps
- Learning path between concepts (BFS)
- Readiness scoring
"""
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class LearningGraph:
    """
    Graf zależności między konceptami
    """

    def __init__(self, knowledge_base: Dict[str, Any]):
        """
        Args:
            knowledge_base: Dict z konceptami
        """
        self.knowledge_base = knowledge_base
        self.concepts = knowledge_base.get("concepts", {})

        # Build graphs
        self.prerequisite_graph = {}  # concept -> list of prerequisites
        self.next_steps_graph = {}    # concept -> list of next_steps

        self._build_dependency_graphs()

    def _build_dependency_graphs(self):
        """Buduj grafy zależności z knowledge base"""
        for concept_id, concept_def in self.concepts.items():
            # Prerequisites graph
            prerequisites = concept_def.get("prerequisites", [])
            self.prerequisite_graph[concept_id] = prerequisites

            # Next steps graph
            next_steps = concept_def.get("next_steps", [])
            self.next_steps_graph[concept_id] = next_steps

    def get_available_next_steps(
        self,
        mastered_concepts: List[str],
        in_progress_concepts: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Znajdź koncepty do których użytkownik jest gotowy

        Args:
            mastered_concepts: Lista ID konceptów które są opanowane (mastery_level >= 3)
            in_progress_concepts: Lista ID konceptów które są w trakcie (mastery_level 1-2)
            max_results: Max liczba wyników

        Returns:
            Lista dict-ów z dostępnymi next steps:
            [
                {
                    "concept_id": "fastapi_dependencies",
                    "name": "FastAPI Dependencies",
                    "category": "Backend",
                    "difficulty": 3,
                    "ready": True,  # wszystkie prerequisites spełnione
                    "prerequisites_met": 2,
                    "prerequisites_total": 2,
                    "readiness_score": 1.0,
                    "sources": ["fastapi_routing"]  # skąd przyszła sugestia
                },
                ...
            ]
        """
        if in_progress_concepts is None:
            in_progress_concepts = []

        all_learned = set(mastered_concepts + in_progress_concepts)
        available = []

        # Zbierz all possible next steps z opanowanych konceptów
        candidate_concepts = set()
        for mastered_id in mastered_concepts:
            next_steps = self.next_steps_graph.get(mastered_id, [])
            for next_id in next_steps:
                if next_id not in all_learned:
                    candidate_concepts.add((next_id, mastered_id))

        # Sprawdź readiness dla każdego kandydata
        readiness_scores = {}
        for concept_id, source_id in candidate_concepts:
            if concept_id not in readiness_scores:
                readiness = self.calculate_readiness(concept_id, all_learned)
                readiness_scores[concept_id] = {
                    **readiness,
                    "sources": [source_id]
                }
            else:
                readiness_scores[concept_id]["sources"].append(source_id)

        # Sortuj po readiness score (malejąco) i difficulty (rosnąco)
        for concept_id, data in readiness_scores.items():
            if concept_id not in self.concepts:
                continue

            concept_def = self.concepts[concept_id]

            available.append({
                "concept_id": concept_id,
                "name": concept_def["name"],
                "category": concept_def["category"],
                "subcategory": concept_def.get("subcategory", ""),
                "difficulty": concept_def.get("difficulty", 3),
                "ready": data["ready"],
                "prerequisites_met": data["prerequisites_met"],
                "prerequisites_total": data["prerequisites_total"],
                "readiness_score": data["readiness_score"],
                "sources": data["sources"][:3]  # Max 3 sources
            })

        # Sortuj: gotowe pierwsze, potem po readiness_score, potem po difficulty
        available.sort(key=lambda x: (
            not x["ready"],  # False (ready) przed True (not ready)
            -x["readiness_score"],  # Wyższy score pierwszy
            x["difficulty"]  # Łatwiejsze pierwsze
        ))

        return available[:max_results]

    def calculate_readiness(
        self,
        concept_id: str,
        learned_concepts: Set[str]
    ) -> Dict[str, Any]:
        """
        Oblicz gotowość użytkownika do nauki konceptu

        Args:
            concept_id: ID konceptu
            learned_concepts: Set ID konceptów które użytkownik zna

        Returns:
            {
                "ready": True/False,  # wszystkie prerequisites spełnione
                "prerequisites_met": 2,
                "prerequisites_total": 3,
                "readiness_score": 0.67  # met / total
            }
        """
        prerequisites = self.prerequisite_graph.get(concept_id, [])

        if not prerequisites:
            # Brak prerequisites - ready
            return {
                "ready": True,
                "prerequisites_met": 0,
                "prerequisites_total": 0,
                "readiness_score": 1.0
            }

        met = sum(1 for p in prerequisites if p in learned_concepts)
        total = len(prerequisites)
        score = met / total if total > 0 else 0.0

        return {
            "ready": met == total,
            "prerequisites_met": met,
            "prerequisites_total": total,
            "readiness_score": score
        }

    def get_learning_path(
        self,
        from_concept: str,
        to_concept: str,
        learned_concepts: Optional[Set[str]] = None
    ) -> Optional[List[str]]:
        """
        Znajdź najkrótszą ścieżkę uczenia się między konceptami (BFS)

        Args:
            from_concept: Koncepty który użytkownik już zna
            to_concept: Koncept docelowy
            learned_concepts: Set konceptów które użytkownik już zna (optional)

        Returns:
            Lista ID konceptów (ścieżka) lub None jeśli nie ma ścieżki
            Np. ["python_basics", "python_async", "fastapi_routing", "fastapi_async"]
        """
        if learned_concepts is None:
            learned_concepts = set()

        if from_concept == to_concept:
            return [from_concept]

        # BFS
        queue = deque([(from_concept, [from_concept])])
        visited = {from_concept}

        while queue:
            current, path = queue.popleft()

            # Sprawdź next_steps
            next_steps = self.next_steps_graph.get(current, [])

            for next_id in next_steps:
                if next_id in visited:
                    continue

                new_path = path + [next_id]

                if next_id == to_concept:
                    return new_path

                visited.add(next_id)
                queue.append((next_id, new_path))

        # Nie znaleziono ścieżki
        return None

    def get_prerequisite_tree(
        self,
        concept_id: str,
        learned_concepts: Optional[Set[str]] = None,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Zwróć drzewo prerequisitów dla konceptu

        Args:
            concept_id: ID konceptu
            learned_concepts: Set konceptów które użytkownik już zna
            max_depth: Maksymalna głębokość drzewa

        Returns:
            Dict z drzewem:
            {
                "concept_id": "fastapi_async",
                "name": "FastAPI Async",
                "learned": False,
                "prerequisites": [
                    {
                        "concept_id": "fastapi_routing",
                        "name": "FastAPI Routing",
                        "learned": True,
                        "prerequisites": [...]
                    },
                    {
                        "concept_id": "python_async",
                        "name": "Python Async",
                        "learned": False,
                        "prerequisites": [...]
                    }
                ]
            }
        """
        if learned_concepts is None:
            learned_concepts = set()

        def build_tree(cid: str, depth: int) -> Dict[str, Any]:
            if depth > max_depth or cid not in self.concepts:
                return None

            concept_def = self.concepts[cid]
            prerequisites = self.prerequisite_graph.get(cid, [])

            tree = {
                "concept_id": cid,
                "name": concept_def["name"],
                "category": concept_def["category"],
                "learned": cid in learned_concepts,
                "prerequisites": []
            }

            if depth < max_depth and prerequisites:
                for prereq_id in prerequisites:
                    subtree = build_tree(prereq_id, depth + 1)
                    if subtree:
                        tree["prerequisites"].append(subtree)

            return tree

        return build_tree(concept_id, 0)

    def get_all_prerequisites(self, concept_id: str) -> Set[str]:
        """
        Zwróć wszystkie prerequisites konceptu (rekurencyjnie)

        Args:
            concept_id: ID konceptu

        Returns:
            Set wszystkich ID prerequisitów
        """
        all_prereqs = set()
        visited = set()

        def collect_prereqs(cid: str):
            if cid in visited:
                return
            visited.add(cid)

            prerequisites = self.prerequisite_graph.get(cid, [])
            for prereq_id in prerequisites:
                all_prereqs.add(prereq_id)
                collect_prereqs(prereq_id)

        collect_prereqs(concept_id)
        return all_prereqs

    def get_concepts_by_category(self, category: str) -> List[str]:
        """
        Zwróć wszystkie koncepty z danej kategorii

        Args:
            category: Nazwa kategorii (np. "Backend", "Frontend")

        Returns:
            Lista ID konceptów
        """
        return [
            cid for cid, cdef in self.concepts.items()
            if cdef.get("category") == category
        ]

    def get_concepts_by_difficulty(self, min_diff: int = 1, max_diff: int = 5) -> List[str]:
        """
        Zwróć koncepty w zakresie trudności

        Args:
            min_diff: Min difficulty (1-5)
            max_diff: Max difficulty (1-5)

        Returns:
            Lista ID konceptów
        """
        return [
            cid for cid, cdef in self.concepts.items()
            if min_diff <= cdef.get("difficulty", 3) <= max_diff
        ]


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test learning graph"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from data_manager import load_knowledge_base

    print("Testing learning_graph.py...")

    # Load knowledge base
    kb = load_knowledge_base()

    if not kb.get("concepts"):
        print("❌ Knowledge base jest pusty")
        sys.exit(1)

    print(f"\n✅ Loaded {len(kb['concepts'])} concepts")

    # Build graph
    graph = LearningGraph(kb)

    # Test: Get available next steps
    mastered = ["python_basics", "fastapi_routing", "sqlalchemy_models"]
    print(f"\n🎯 Mastered concepts: {mastered}")

    next_steps = graph.get_available_next_steps(mastered, max_results=5)
    print(f"\n📚 Available next steps ({len(next_steps)}):")
    for step in next_steps:
        ready_icon = "✅" if step["ready"] else "⏳"
        print(f"  {ready_icon} {step['name']} ({step['category']}) - difficulty={step['difficulty']}, readiness={step['readiness_score']:.0%}")

    # Test: Learning path
    if "python_basics" in kb["concepts"] and "langchain_chains" in kb["concepts"]:
        path = graph.get_learning_path("python_basics", "langchain_chains")
        if path:
            print(f"\n🛤️  Learning path (python_basics → langchain_chains):")
            print(f"  {' → '.join(path)}")

    # Test: Prerequisite tree
    if "fastapi_async" in kb["concepts"]:
        tree = graph.get_prerequisite_tree("fastapi_async", learned_concepts=set(mastered), max_depth=2)
        print(f"\n🌳 Prerequisite tree for 'fastapi_async':")

        def print_tree(node, indent=0):
            learned_icon = "✅" if node.get("learned") else "⏳"
            print(f"  {'  ' * indent}{learned_icon} {node['name']} ({node['concept_id']})")
            for prereq in node.get("prerequisites", []):
                print_tree(prereq, indent + 1)

        print_tree(tree)
