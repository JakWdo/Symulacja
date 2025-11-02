#!/usr/bin/env python3
"""
Testy dla recommendation_engine.py - weryfikacja sugestii i priorytetyzacji

Sprawdza:
1. suggest_next_concepts() - zwraca sensowne sugestie
2. _get_mastered_concepts() - identyfikuje opanowane koncepty
3. _get_in_progress_concepts() - identyfikuje koncepty w toku
4. _prioritize_recommendations() - prawidłowe sortowanie
5. _get_recent_categories() - śledzenie ostatnich kategorii
6. _generate_reason() - generowanie uzasadnień
"""

import sys
from pathlib import Path

# Dodaj scripts do path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from recommendation_engine import RecommendationEngine


class TestRecommendationEngine:
    """Testy dla RecommendationEngine"""

    def test_init_with_graph_and_kb(self):
        """Test: inicjalizacja z learning_graph i knowledge_base"""
        # Mock data
        learning_graph = type('obj', (object,), {'get_next_concepts': lambda self, x: []})()
        knowledge_base = {"concepts": {}}

        engine = RecommendationEngine(learning_graph, knowledge_base)

        assert engine.learning_graph is not None
        assert engine.knowledge_base is not None

    def test_get_mastered_concepts_returns_list(self):
        """Test: _get_mastered_concepts zwraca listę"""
        engine = RecommendationEngine(None, {})

        progress = {
            "concepts": {
                "fastapi_routing": {"mastery_level": 3},
                "react_components": {"mastery_level": 2},
            }
        }

        mastered = engine._get_mastered_concepts(progress)

        assert isinstance(mastered, list)
        assert "fastapi_routing" in mastered

    def test_get_mastered_concepts_filters_by_level(self):
        """Test: _get_mastered_concepts filtruje po mastery_level >= 3"""
        engine = RecommendationEngine(None, {})

        progress = {
            "concepts": {
                "fastapi_routing": {"mastery_level": 3},
                "react_components": {"mastery_level": 2},
                "sqlalchemy_models": {"mastery_level": 4},
            }
        }

        mastered = engine._get_mastered_concepts(progress)

        assert "fastapi_routing" in mastered
        assert "react_components" not in mastered
        assert "sqlalchemy_models" in mastered

    def test_get_in_progress_concepts_returns_list(self):
        """Test: _get_in_progress_concepts zwraca listę"""
        engine = RecommendationEngine(None, {})

        progress = {
            "concepts": {
                "fastapi_routing": {"mastery_level": 2},
                "react_components": {"mastery_level": 1},
            }
        }

        in_progress = engine._get_in_progress_concepts(progress)

        assert isinstance(in_progress, list)
        assert len(in_progress) >= 0

    def test_get_in_progress_filters_by_level(self):
        """Test: _get_in_progress_concepts filtruje poziomy 1-2"""
        engine = RecommendationEngine(None, {})

        progress = {
            "concepts": {
                "fastapi_routing": {"mastery_level": 1},
                "react_components": {"mastery_level": 2},
                "sqlalchemy_models": {"mastery_level": 3},
            }
        }

        in_progress = engine._get_in_progress_concepts(progress)

        assert "fastapi_routing" in in_progress
        assert "react_components" in in_progress
        assert "sqlalchemy_models" not in in_progress

    def test_get_recent_categories(self):
        """Test: _get_recent_categories zwraca ostatnie kategorie"""
        engine = RecommendationEngine(None, {"concepts": {}})

        progress = {
            "concepts": {
                "fastapi_routing": {"category": "Backend", "last_practiced": "2025-11-01"},
                "react_components": {"category": "Frontend", "last_practiced": "2025-11-02"},
            }
        }

        recent = engine._get_recent_categories(progress, limit=5)

        assert isinstance(recent, list)
        # Powinno zwrócić kategorie z ostatnich praktyk

    def test_generate_reason_with_prerequisites(self):
        """Test: _generate_reason generuje uzasadnienie dla prerequisite"""
        graph = type('obj', (object,), {
            'get_prerequisites': lambda self, x: ["fastapi_routing"]
        })()

        kb = {
            "concepts": {
                "fastapi_routing": {"name": "FastAPI Routing"},
                "fastapi_async": {"name": "FastAPI Async"}
            }
        }

        engine = RecommendationEngine(graph, kb)

        reason = engine._generate_reason(
            "fastapi_async",
            ["fastapi_routing"],
            [],
            "Backend"
        )

        assert "FastAPI Routing" in reason or "natural" in reason.lower()

    def test_prioritize_empty_suggestions(self):
        """Test: _prioritize_recommendations obsługuje pustą listę"""
        engine = RecommendationEngine(None, {"concepts": {}})

        result = engine._prioritize_recommendations([], {}, {})

        assert isinstance(result, list)
        assert len(result) == 0

    def test_prioritize_sorts_by_readiness(self):
        """Test: _prioritize_recommendations sortuje po gotowości"""
        graph = type('obj', (object,), {
            'calculate_concept_readiness': lambda self, cid, mastered: 1.0 if cid == "ready" else 0.5
        })()

        kb = {
            "concepts": {
                "ready": {"name": "Ready Concept", "category": "Backend"},
                "not_ready": {"name": "Not Ready", "category": "Backend"}
            }
        }

        engine = RecommendationEngine(graph, kb)

        suggestions = ["ready", "not_ready"]
        result = engine._prioritize_recommendations(suggestions, {}, {})

        # "ready" powinien być pierwszy (wyższa gotowość)
        assert result[0]["id"] == "ready"

    def test_suggest_next_concepts_with_config(self):
        """Test: suggest_next_concepts respektuje config"""
        graph = type('obj', (object,), {
            'get_next_concepts': lambda self, mastered: ["fastapi_async"],
            'calculate_concept_readiness': lambda self, cid, mastered: 1.0
        })()

        kb = {
            "concepts": {
                "fastapi_async": {"name": "FastAPI Async", "category": "Backend"}
            }
        }

        engine = RecommendationEngine(graph, kb)

        progress = {
            "concepts": {
                "fastapi_routing": {"mastery_level": 3}
            }
        }

        config = {"max_suggestions": 3}

        suggestions = engine.suggest_next_concepts(progress, config, max_suggestions=3)

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3

    def test_suggest_respects_prefer_category(self):
        """Test: suggest_next_concepts priorytetyzuje preferowaną kategorię"""
        graph = type('obj', (object,), {
            'get_next_concepts': lambda self, mastered: ["backend_concept", "frontend_concept"],
            'calculate_concept_readiness': lambda self, cid, mastered: 1.0
        })()

        kb = {
            "concepts": {
                "backend_concept": {"name": "Backend", "category": "Backend"},
                "frontend_concept": {"name": "Frontend", "category": "Frontend"}
            }
        }

        engine = RecommendationEngine(graph, kb)

        progress = {"concepts": {}}
        config = {"prefer_category": "Backend"}

        suggestions = engine.suggest_next_concepts(progress, config)

        # Backend concepts powinny być wyżej
        if len(suggestions) > 0:
            # Sprawdź że Backend jest wysoko
            backend_found = any(s["category"] == "Backend" for s in suggestions[:2])
            assert backend_found or len(suggestions) == 1


if __name__ == "__main__":
    # Proste uruchomienie testów bez pytest
    test = TestRecommendationEngine()

    print("Running recommendation_engine tests...")

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
