#!/usr/bin/env python3
"""
Concept Manager - Unified interface dla wszystkich konceptów

Łączy:
- Static concepts (z knowledge_base.json)
- Dynamic concepts (z dynamic_concepts.json - auto-discovered)
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConceptManager:
    """
    Zarządza wszystkimi konceptami (static + dynamic)
    """

    def __init__(self, knowledge_base: Dict[str, Any], dynamic_concepts: Dict[str, Any]):
        """
        Args:
            knowledge_base: Dict z knowledge_base.json
            dynamic_concepts: Dict z dynamic_concepts.json
        """
        self.knowledge_base = knowledge_base
        self.dynamic_concepts = dynamic_concepts

    def get_all_concepts(self) -> Dict[str, Any]:
        """
        Zwróć wszystkie koncepty (static + dynamic merged)

        Returns:
            Dict z wszystkimi konceptami
        """
        static = self.knowledge_base.get("concepts", {})
        return {**static, **self.dynamic_concepts}

    def get_static_concepts(self) -> Dict[str, Any]:
        """Zwróć tylko static concepts"""
        return self.knowledge_base.get("concepts", {})

    def get_dynamic_concepts(self) -> Dict[str, Any]:
        """Zwróć tylko dynamic concepts"""
        return self.dynamic_concepts

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Pobierz pojedynczy koncept (static lub dynamic)

        Args:
            concept_id: ID konceptu

        Returns:
            Concept definition lub None
        """
        all_concepts = self.get_all_concepts()
        return all_concepts.get(concept_id)

    def is_dynamic(self, concept_id: str) -> bool:
        """
        Sprawdź czy koncept jest auto-discovered

        Args:
            concept_id: ID konceptu

        Returns:
            True jeśli dynamic
        """
        return concept_id in self.dynamic_concepts

    def get_categories(self) -> Dict[str, Any]:
        """
        Zwróć wszystkie kategorie

        Returns:
            Dict z kategoriami
        """
        return self.knowledge_base.get("categories", {})

    def get_concepts_by_category(self, category: str) -> Dict[str, Any]:
        """
        Zwróć koncepty z danej kategorii

        Args:
            category: Nazwa kategorii

        Returns:
            Dict z konceptami
        """
        all_concepts = self.get_all_concepts()
        return {
            cid: cdef for cid, cdef in all_concepts.items()
            if cdef.get("category") == category
        }

    def promote_to_static(self, concept_id: str) -> bool:
        """
        Promuj dynamic concept do static knowledge_base
        (Dla konceptów które są często używane i dobrze zdefiniowane)

        Args:
            concept_id: ID konceptu do promowania

        Returns:
            True jeśli sukces
        """
        if concept_id not in self.dynamic_concepts:
            logger.warning(f"Concept {concept_id} nie jest dynamic")
            return False

        concept = self.dynamic_concepts[concept_id]

        # Walidacja: czy koncept ma wystarczającą jakość
        meta = concept.get("discovery_metadata", {})
        confidence = meta.get("confidence", 0.0)
        count = meta.get("discovery_count", 0)

        if confidence < 0.85 or count < 15:
            logger.info(f"Concept {concept_id} nie jest gotowy do promocji (confidence={confidence}, count={count})")
            return False

        # Dodaj do static
        self.knowledge_base["concepts"][concept_id] = concept

        # Usuń z dynamic
        del self.dynamic_concepts[concept_id]

        logger.info(f"✅ Promoted {concept_id} to static knowledge base")
        return True


# ============================================================================
# Utility functions
# ============================================================================

def get_concept_manager() -> ConceptManager:
    """
    Pomocnicza funkcja - zwróć ConceptManager instance

    Returns:
        ConceptManager
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from data_manager import load_knowledge_base, load_dynamic_concepts

    kb = load_knowledge_base()
    dynamic = load_dynamic_concepts()

    return ConceptManager(kb, dynamic)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    """Test concept manager"""
    print("Testing concept_manager.py...")

    manager = get_concept_manager()

    all_concepts = manager.get_all_concepts()
    static = manager.get_static_concepts()
    dynamic = manager.get_dynamic_concepts()

    print(f"\n📚 Total concepts: {len(all_concepts)}")
    print(f"   Static: {len(static)}")
    print(f"   Dynamic: {len(dynamic)}")

    if dynamic:
        print(f"\n⭐ Auto-discovered concepts:")
        for cid, cdef in list(dynamic.items())[:5]:
            print(f"   • {cdef['name']} ({cdef['category']})")
