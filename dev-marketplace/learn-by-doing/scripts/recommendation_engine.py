#!/usr/bin/env python3
"""
Recommendation Engine - Aktywne sugestie co uczyć się dalej

Funkcjonalność:
- Priorytetyzacja next steps na podstawie kontekstu
- Generowanie uzasadnień ("dlaczego")
- Filtrowanie po category preference
- Uwzględnianie ostatnich aktywności
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generuje rekomendacje co uczyć się dalej
    """

    def __init__(
        self,
        knowledge_base: Dict[str, Any],
        learning_graph: Any  # LearningGraph instance
    ):
        """
        Args:
            knowledge_base: Dict z konceptami
            learning_graph: Instance LearningGraph
        """
        self.knowledge_base = knowledge_base
        self.learning_graph = learning_graph
        self.concepts = knowledge_base.get("concepts", {})

    def suggest_next_concepts(
        self,
        user_progress: Dict[str, Any],
        config: Dict[str, Any],
        domain_id: Optional[str] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generuj sugestie co uczyć się dalej

        Args:
            user_progress: Dict z postępem użytkownika (z learning_progress.json)
            config: Dict z konfiguracją (z config.json)
            domain_id: Opcjonalne - filtruj tylko do tej dziedziny
            max_suggestions: Max liczba sugestii

        Returns:
            Lista sugestii:
            [
                {
                    "concept_id": "fastapi_dependencies",
                    "name": "FastAPI Dependencies",
                    "domain": "backend",
                    "difficulty": 3,
                    "ready": True,
                    "reason": "Opanowałeś FastAPI Routing, to naturalny następny krok",
                    "priority": 1  # 1-5 (1=highest)
                },
                ...
            ]
        """
        if not config.get("recommendations", {}).get("enabled", True):
            return []

        # Zbierz context
        mastered = self._get_mastered_concepts(user_progress)
        in_progress = self._get_in_progress_concepts(user_progress)

        # Get available next steps z learning graph
        available = self.learning_graph.get_available_next_steps(
            mastered_concepts=mastered,
            in_progress_concepts=in_progress,
            max_results=max_suggestions * 3  # Get więcej żeby móc priorytetyzować
        )

        # Filtruj po dziedzinie jeśli podana
        if domain_id:
            available = [
                rec for rec in available
                if self.concepts.get(rec['concept_id'], {}).get('domain') == domain_id
            ]

        # Priorytetyzuj
        prioritized = self._prioritize_recommendations(
            available,
            user_progress,
            config,
            domain_id
        )

        # Generate reasons
        for rec in prioritized:
            rec["reason"] = self._generate_reason(rec, user_progress, mastered)

        return prioritized[:max_suggestions]

    def _get_mastered_concepts(self, user_progress: Dict[str, Any]) -> List[str]:
        """
        Zwróć listę opanowanych konceptów (mastery_level >= 3)

        Args:
            user_progress: Dict z postępem

        Returns:
            Lista ID konceptów
        """
        concepts = user_progress.get("concepts", {})
        return [
            concept_id for concept_id, data in concepts.items()
            if data.get("mastery_level", 0) >= 3
        ]

    def _get_in_progress_concepts(self, user_progress: Dict[str, Any]) -> List[str]:
        """
        Zwróć listę konceptów w trakcie (mastery_level 1-2)

        Args:
            user_progress: Dict z postępem

        Returns:
            Lista ID konceptów
        """
        concepts = user_progress.get("concepts", {})
        return [
            concept_id for concept_id, data in concepts.items()
            if 1 <= data.get("mastery_level", 0) < 3
        ]

    def _prioritize_recommendations(
        self,
        available: List[Dict[str, Any]],
        user_progress: Dict[str, Any],
        config: Dict[str, Any],
        domain_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Priorytetyzuj rekomendacje

        Kryteria (w kolejności):
        1. Ready vs not ready (gotowe pierwsze)
        2. Domain preference (jeśli podana)
        3. Recent activity (co robił ostatnio)
        4. Difficulty (nie za duży skok)
        5. Readiness score

        Args:
            available: Lista dostępnych next steps z learning_graph
            user_progress: Dict z postępem
            config: Dict z konfiguracją
            domain_id: Opcjonalne - preferowana dziedzina

        Returns:
            Posortowana lista z priority (1-5)
        """
        # Oblicz recent domains (co robił ostatnio)
        recent_domains = self._get_recent_domains(user_progress)

        # Score każdej rekomendacji
        scored = []
        for rec in available:
            score = 0.0

            # 1. Ready bonus (+10)
            if rec.get("ready", False):
                score += 10.0

            # 2. Domain preference (+5 jeśli pasuje do focus)
            rec_domain = self.concepts.get(rec['concept_id'], {}).get('domain')
            if domain_id and rec_domain == domain_id:
                score += 5.0

            # 3. Recent activity bonus (+3 jeśli w tej dziedzinie pracował ostatnio)
            if recent_domains and rec_domain in recent_domains[:2]:
                score += 3.0

            # 4. Difficulty penalty (łatwiejsze pierwsze)
            # Penalty: 0 dla difficulty 1-3, -1 dla 4, -2 dla 5
            difficulty = rec.get("difficulty", 3)
            if difficulty > 3:
                score -= (difficulty - 3)

            # 5. Readiness bonus
            score += rec.get("readiness_score", 0.0) * 2.0

            scored.append({
                **rec,
                "score": score,
                "domain": rec_domain
            })

        # Sortuj po score (malejąco)
        scored.sort(key=lambda x: -x["score"])

        # Assign priority (1-5)
        for i, rec in enumerate(scored):
            rec["priority"] = min(i + 1, 5)

        return scored

    def _get_recent_domains(self, user_progress: Dict[str, Any], limit: int = 5) -> List[str]:
        """
        Zwróć dziedziny w których użytkownik pracował ostatnio

        Args:
            user_progress: Dict z postępem
            limit: Max liczba dziedzin

        Returns:
            Lista dziedzin (sorted by frequency)
        """
        concepts = user_progress.get("concepts", {})

        # Zbierz dziedziny z ostatnich praktyk
        domains = []
        for concept_id, data in concepts.items():
            last_practiced = data.get("last_practiced")
            if last_practiced and concept_id in self.concepts:
                domain = self.concepts[concept_id].get("domain")
                if domain:
                    domains.append(domain)

        # Count frequency
        if not domains:
            return []

        domain_counts = Counter(domains)
        return [dom for dom, count in domain_counts.most_common(limit)]

    def _generate_reason(
        self,
        recommendation: Dict[str, Any],
        user_progress: Dict[str, Any],
        mastered: List[str]
    ) -> str:
        """
        Generuj uzasadnienie dla rekomendacji

        Args:
            recommendation: Dict z rekomendacją
            user_progress: Dict z postępem
            mastered: Lista opanowanych konceptów

        Returns:
            String z uzasadnieniem
        """
        concept_id = recommendation["concept_id"]
        ready = recommendation.get("ready", False)
        sources = recommendation.get("sources", [])
        domain = recommendation.get("domain", "")

        # Sprawdź sources
        source_names = []
        for source_id in sources[:2]:
            if source_id in self.concepts:
                source_names.append(self.concepts[source_id]["name"])

        # Generuj reason na podstawie context
        if not ready:
            # Nie gotowy - wymaga więcej prerequisites
            prereqs_total = recommendation.get("prerequisites_total", 0)
            prereqs_met = recommendation.get("prerequisites_met", 0)
            missing = prereqs_total - prereqs_met
            return f"Wymaga {missing} więcej prerequisitów. Kontynuuj naukę podstaw."

        if source_names:
            # Ma źródła - naturalny next step
            if len(source_names) == 1:
                return f"Opanowałeś {source_names[0]}, to naturalny następny krok"
            else:
                return f"Opanowałeś {source_names[0]} i {source_names[1]}, to naturalny następny krok"

        # Ogólne uzasadnienie
        if domain:
            domain_names = {
                "backend": "Backend Development",
                "frontend": "Frontend Development",
                "ai_ml": "AI & Machine Learning",
                "databases": "Databases",
                "devops": "DevOps",
                "testing": "Testing",
                "system_design": "System Design"
            }
            domain_name = domain_names.get(domain, domain)
            return f"Rozszerz swoje umiejętności w {domain_name}"

        return "Gotowe do nauki"


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    """Test recommendation engine"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from data_manager import load_knowledge_base, load_progress, load_config
    from learning_graph import LearningGraph

    print("Testing recommendation_engine.py...")

    # Load data
    kb = load_knowledge_base()
    progress = load_progress()
    config = load_config()

    if not kb.get("concepts"):
        print("❌ Knowledge base jest pusty")
        sys.exit(1)

    print(f"\n✅ Loaded {len(kb['concepts'])} concepts")

    # Build graph
    graph = LearningGraph(kb)

    # Build engine
    engine = RecommendationEngine(kb, graph)

    # Mock progress (dla testu)
    if not progress.get("concepts"):
        print("\n⚠️  Brak konceptów w progress, używam mock danych")
        progress["concepts"] = {
            "python_basics": {"mastery_level": 5, "last_practiced": "2025-11-01T10:00:00"},
            "fastapi_routing": {"mastery_level": 4, "last_practiced": "2025-11-02T09:00:00"},
            "sqlalchemy_models": {"mastery_level": 3, "last_practiced": "2025-11-02T08:00:00"}
        }
        progress["current_focus"] = {"category": "Backend"}

    # Get recommendations
    recommendations = engine.suggest_next_concepts(progress, config, max_suggestions=5)

    print(f"\n💡 Recommendations ({len(recommendations)}):")
    for rec in recommendations:
        ready_icon = "✅" if rec.get("ready") else "⏳"
        print(f"  {ready_icon} P{rec['priority']} - {rec['name']} ({rec['category']})")
        print(f"       → {rec['reason']}")
