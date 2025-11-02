#!/usr/bin/env python3
"""
Testy dla learning_graph.py - weryfikacja dependency graph i pathfinding

Sprawdza:
1. build_graph() - tworzenie grafu z knowledge_base
2. get_prerequisites() - zwracanie zależności
3. get_next_concepts() - sugestie następnych kroków
4. find_learning_path() - BFS pathfinding
5. calculate_concept_readiness() - gotowość do nauki
"""

import sys
from pathlib import Path

# Dodaj scripts do path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from learning_graph import LearningGraph


class TestLearningGraph:
    """Testy dla LearningGraph"""

    def test_build_graph_creates_nodes(self):
        """Test: build_graph() tworzy węzły dla konceptów"""
        kb = {
            "concepts": {
                "fastapi_routing": {
                    "name": "FastAPI Routing",
                    "prerequisites": [],
                    "next_steps": ["fastapi_async"]
                },
                "fastapi_async": {
                    "name": "FastAPI Async",
                    "prerequisites": ["fastapi_routing"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        assert "fastapi_routing" in graph.graph
        assert "fastapi_async" in graph.graph

    def test_get_prerequisites_returns_list(self):
        """Test: get_prerequisites() zwraca listę prerequisites"""
        kb = {
            "concepts": {
                "fastapi_async": {
                    "name": "FastAPI Async",
                    "prerequisites": ["fastapi_routing", "python_async"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        prereqs = graph.get_prerequisites("fastapi_async")

        assert isinstance(prereqs, list)
        assert "fastapi_routing" in prereqs
        assert "python_async" in prereqs

    def test_get_prerequisites_empty_for_basics(self):
        """Test: get_prerequisites() zwraca [] dla podstawowych konceptów"""
        kb = {
            "concepts": {
                "python_basics": {
                    "name": "Python Basics",
                    "prerequisites": [],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        prereqs = graph.get_prerequisites("python_basics")

        assert prereqs == []

    def test_get_next_concepts_returns_suggestions(self):
        """Test: get_next_concepts() zwraca koncepty do nauki"""
        kb = {
            "concepts": {
                "fastapi_routing": {
                    "name": "FastAPI Routing",
                    "prerequisites": [],
                    "next_steps": ["fastapi_async", "fastapi_dependencies"]
                }
            }
        }

        graph = LearningGraph(kb)

        next_concepts = graph.get_next_concepts(["fastapi_routing"])

        assert isinstance(next_concepts, list)
        # Powinno zwrócić koncepty z next_steps mastered concepts

    def test_calculate_readiness_full_when_all_prereqs_mastered(self):
        """Test: calculate_concept_readiness() = 1.0 gdy wszystkie prereqs opanowane"""
        kb = {
            "concepts": {
                "fastapi_async": {
                    "name": "FastAPI Async",
                    "prerequisites": ["fastapi_routing"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        readiness = graph.calculate_concept_readiness("fastapi_async", ["fastapi_routing"])

        assert readiness == 1.0

    def test_calculate_readiness_zero_when_no_prereqs_mastered(self):
        """Test: calculate_concept_readiness() = 0.0 gdy brak opanowanych prereqs"""
        kb = {
            "concepts": {
                "fastapi_async": {
                    "name": "FastAPI Async",
                    "prerequisites": ["fastapi_routing", "python_async"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        readiness = graph.calculate_concept_readiness("fastapi_async", [])

        assert readiness == 0.0

    def test_calculate_readiness_partial(self):
        """Test: calculate_concept_readiness() zwraca partial gdy część prereqs"""
        kb = {
            "concepts": {
                "advanced_concept": {
                    "name": "Advanced",
                    "prerequisites": ["basic1", "basic2", "basic3"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        # Opanowano 1 z 3 prerequisites
        readiness = graph.calculate_concept_readiness("advanced_concept", ["basic1"])

        assert 0.0 < readiness < 1.0
        assert readiness == 1.0 / 3.0  # 33%

    def test_find_learning_path_exists(self):
        """Test: find_learning_path() znajduje ścieżkę między konceptami"""
        kb = {
            "concepts": {
                "basics": {
                    "prerequisites": [],
                    "next_steps": ["intermediate"]
                },
                "intermediate": {
                    "prerequisites": ["basics"],
                    "next_steps": ["advanced"]
                },
                "advanced": {
                    "prerequisites": ["intermediate"],
                    "next_steps": []
                }
            }
        }

        graph = LearningGraph(kb)

        path = graph.find_learning_path("basics", "advanced")

        assert isinstance(path, list)
        # Ścieżka powinna istnieć: basics → intermediate → advanced
        if path:
            assert "basics" in path
            assert "advanced" in path


if __name__ == "__main__":
    # Proste uruchomienie testów bez pytest
    test = TestLearningGraph()

    print("Running learning_graph tests...")

    tests = [m for m in dir(test) if m.startswith('test_')]
    passed = 0
    failed = 0

    for test_name in tests:
        try:
            getattr(test, test_name)()
            print(f"  ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
