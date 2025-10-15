#!/usr/bin/env python3
"""
Legacy MENTIONS Cleanup Script

Usuwa legacy data z archived feature (graph_service.py):
- MENTIONS relationships (2757 relacji)
- Concept nodes (20)
- Emotion nodes (1)
- Persona nodes NIE używane przez personas table

Funkcjonalności:
- Pre-cleanup verification (count legacy data)
- Batch delete dla performance
- Post-cleanup verification (verify RAG nodes intact)
- --dry-run mode (sprawdza co zostanie usunięte bez wykonywania cleanup)
- Detailed logging i summary report

Uruchomienie:
    # WAŻNE: Zawsze najpierw zrób backup!
    python scripts/backup_neo4j.py

    # Dry-run (bezpieczny podgląd)
    python scripts/cleanup_legacy_mentions.py --dry-run

    # Właściwy cleanup
    python scripts/cleanup_legacy_mentions.py

Wymaga:
    - Uruchomiony Neo4j (docker-compose up neo4j)
    - Poprawne NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD w .env
    - ZALECANE: Backup utworzony przed cleanup (backup_neo4j.py)
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegacyCleanup:
    """
    Manager do usuwania legacy MENTIONS data z Neo4j.

    Attributes:
        driver: Neo4j driver instance
        dry_run: Czy tryb dry-run (bez zmian)
    """

    def __init__(self, dry_run: bool = False):
        """
        Inicjalizuje cleanup manager.

        Args:
            dry_run: Jeśli True, tylko pokazuje co zostanie zrobione
        """
        self.driver = None
        self.dry_run = dry_run

    def connect(self) -> bool:
        """
        Nawiązuje połączenie z Neo4j.

        Returns:
            True jeśli połączenie udane, False w przeciwnym razie
        """
        logger.info(f"🔌 Łączę się z Neo4j: {settings.NEO4J_URI}")

        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            # Weryfikuj połączenie
            self.driver.verify_connectivity()
            logger.info("✅ Połączono z Neo4j pomyślnie")
            return True

        except Exception as e:
            logger.error(f"❌ BŁĄD: Nie można połączyć się z Neo4j: {e}")
            logger.error("Upewnij się że:")
            logger.error("  1. Neo4j jest uruchomiony: docker-compose up -d neo4j")
            logger.error("  2. NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD są poprawne w .env")
            return False

    def get_pre_cleanup_stats(self) -> Dict[str, Any]:
        """
        Zbiera statystyki PRZED cleanup.

        Returns:
            Dict ze statystykami (counts, labels, relationship types)
        """
        logger.info("📊 Zbieranie statystyk PRE-CLEANUP...")

        with self.driver.session() as session:
            # 1. Total counts
            result = session.run("MATCH (n) RETURN count(n) as count")
            total_nodes = result.single()['count']

            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_rels = result.single()['count']

            # 2. Legacy MENTIONS relationships (Persona → Concept)
            result = session.run("MATCH (p:Persona)-[r:MENTIONS]->(c:Concept) RETURN count(r) as count")
            legacy_mentions_count = result.single()['count']

            # RAG MENTIONS (Document → RAG nodes) - should NOT be deleted
            result = session.run("""
                MATCH (d:Document)-[r:MENTIONS]->(n)
                WHERE n:Wskaznik OR n:Obserwacja OR n:Trend OR n:Demografia OR n:Lokalizacja
                RETURN count(r) as count
            """)
            rag_mentions_count = result.single()['count']

            # 3. Legacy Concept nodes
            result = session.run("MATCH (n:Concept) RETURN count(n) as count")
            concept_count = result.single()['count']

            # 4. Legacy Emotion nodes
            result = session.run("MATCH (n:Emotion) RETURN count(n) as count")
            emotion_count = result.single()['count']

            # 5. Persona nodes (sprawdź które mają doc_id - te są używane)
            result = session.run("""
                MATCH (n:Persona)
                RETURN count(n) as total,
                       count(CASE WHEN n.doc_id IS NOT NULL THEN 1 END) as with_doc_id,
                       count(CASE WHEN n.doc_id IS NULL THEN 1 END) as without_doc_id
            """)
            persona_stats = result.single()

            # 6. All labels
            result = session.run("CALL db.labels()")
            all_labels = [record['label'] for record in result]

            # 7. All relationship types
            result = session.run("CALL db.relationshipTypes()")
            all_rel_types = [record['relationshipType'] for record in result]

            # 8. RAG nodes (should NOT be touched)
            rag_node_types = ['Wskaznik', 'Obserwacja', 'Trend', 'Demografia', 'Lokalizacja', 'RAGChunk']
            rag_counts = {}
            for node_type in rag_node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                rag_counts[node_type] = result.single()['count']

            # 9. RAG relationships (should NOT be touched)
            rag_rel_types = ['OPISUJE', 'DOTYCZY', 'POKAZUJE_TREND', 'ZLOKALIZOWANY_W', 'POWIAZANY_Z']
            rag_rel_counts = {}
            for rel_type in rag_rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                rag_rel_counts[rel_type] = result.single()['count']

            stats = {
                'total_nodes': total_nodes,
                'total_rels': total_rels,
                'legacy_mentions_count': legacy_mentions_count,
                'rag_mentions_count': rag_mentions_count,
                'concept_count': concept_count,
                'emotion_count': emotion_count,
                'persona_total': persona_stats['total'],
                'persona_with_doc_id': persona_stats['with_doc_id'],
                'persona_without_doc_id': persona_stats['without_doc_id'],
                'all_labels': all_labels,
                'all_rel_types': all_rel_types,
                'rag_node_counts': rag_counts,
                'rag_rel_counts': rag_rel_counts
            }

            return stats

    def print_pre_cleanup_summary(self, stats: Dict[str, Any]):
        """
        Wyświetla podsumowanie statystyk PRE-CLEANUP.

        Args:
            stats: Dict ze statystykami z get_pre_cleanup_stats()
        """
        print()
        print("=" * 80)
        print("PRE-CLEANUP STATS")
        print("=" * 80)
        print()

        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Relationships: {stats['total_rels']}")
        print()

        print("-" * 80)
        print("LEGACY DATA (TO BE DELETED)")
        print("-" * 80)
        print(f"Legacy MENTIONS (Persona → Concept): {stats['legacy_mentions_count']}")
        print(f"Concept nodes: {stats['concept_count']}")
        print(f"Emotion nodes: {stats['emotion_count']}")
        print(f"Persona nodes (without doc_id): {stats['persona_without_doc_id']}")
        print()

        total_legacy = (
            stats['legacy_mentions_count'] +
            stats['concept_count'] +
            stats['emotion_count'] +
            stats['persona_without_doc_id']
        )
        print(f"⚠️  TOTAL LEGACY ITEMS TO DELETE: {total_legacy}")
        print()

        print("-" * 80)
        print("RAG DATA (WILL NOT BE DELETED)")
        print("-" * 80)
        print(f"RAG MENTIONS (Document → nodes): {stats['rag_mentions_count']}")
        print("  ℹ️  Te relacje są używane przez RAG system - pozostaną nietknięte")
        print()

        print("-" * 80)
        print("RAG DATA (SHOULD REMAIN INTACT)")
        print("-" * 80)

        print("RAG Nodes:")
        for node_type, count in stats['rag_node_counts'].items():
            print(f"  - {node_type}: {count}")

        print()
        print("RAG Relationships:")
        for rel_type, count in stats['rag_rel_counts'].items():
            print(f"  - {rel_type}: {count}")

        print()

        print("-" * 80)
        print("ALL LABELS")
        print("-" * 80)
        print(", ".join(stats['all_labels']))
        print()

        print("-" * 80)
        print("ALL RELATIONSHIP TYPES")
        print("-" * 80)
        print(", ".join(stats['all_rel_types']))
        print()

    def check_dependencies(self) -> bool:
        """
        Sprawdza czy MENTIONS są używane przez jakieś inne features.

        Returns:
            True jeśli bezpieczne do usunięcia, False jeśli wykryto dependencies
        """
        logger.info("🔍 Sprawdzanie dependencies...")

        with self.driver.session() as session:
            # Sprawdź czy są jakieś nietypowe użycia MENTIONS
            # (poza Persona -> Concept)

            result = session.run("""
                MATCH (a)-[r:MENTIONS]->(b)
                WITH labels(a) as source_labels, labels(b) as target_labels, count(r) as count
                RETURN source_labels, target_labels, count
                ORDER BY count DESC
            """)

            mentions_patterns = list(result)

            if not mentions_patterns:
                logger.info("✅ Brak MENTIONS relationships")
                return True

            logger.info(f"Znaleziono {len(mentions_patterns)} pattern(ów) MENTIONS:")

            legacy_count = 0
            rag_count = 0

            for pattern in mentions_patterns:
                source = pattern['source_labels']
                target = pattern['target_labels']
                count = pattern['count']

                logger.info(f"  - {source} -> {target}: {count} relacji")

                # Expected LEGACY pattern: Persona -> Concept
                if 'Persona' in source and 'Concept' in target:
                    logger.info(f"    ✅ Legacy pattern (DO usuniięcia)")
                    legacy_count += count
                # RAG pattern: Document -> RAG nodes (NIE usuwamy!)
                elif 'Document' in source and any(rag_type in target for rag_type in ['Wskaznik', 'Obserwacja', 'Trend', 'Demografia', 'Lokalizacja']):
                    logger.info(f"    ℹ️  RAG pattern (ZACHOWUJEMY - nie usuwamy)")
                    rag_count += count
                else:
                    logger.warning(f"    ⚠️  Nieznany pattern")

            logger.info(f"\nPodsumowanie:")
            logger.info(f"  - Legacy MENTIONS (do usunięcia): {legacy_count}")
            logger.info(f"  - RAG MENTIONS (zachowujemy): {rag_count}")

            if legacy_count == 0:
                logger.info("✅ Brak legacy MENTIONS do usunięcia - graf już czysty!")

            return True  # Zawsze bezpieczne - usuwamy tylko Persona -> Concept

    def delete_mentions_relationships(self):
        """
        Usuwa TYLKO legacy MENTIONS relationships (Persona → Concept).
        NIE usuwa RAG MENTIONS (Document → RAG nodes).
        """
        if self.dry_run:
            logger.info("[DRY-RUN] Usuwanie legacy MENTIONS relationships (Persona → Concept)...")
            return

        logger.info("🗑️  Usuwanie legacy MENTIONS relationships (Persona → Concept)...")

        with self.driver.session() as session:
            # Batch delete dla performance (1000 na raz)
            # ONLY delete Persona -> Concept (legacy)
            deleted_total = 0

            while True:
                result = session.run("""
                    MATCH (p:Persona)-[r:MENTIONS]->(c:Concept)
                    WITH r LIMIT 1000
                    DELETE r
                    RETURN count(r) as deleted
                """)

                deleted = result.single()['deleted']
                deleted_total += deleted

                logger.info(f"  Usunięto {deleted} legacy MENTIONS (total: {deleted_total})")

                if deleted == 0:
                    break

        logger.info(f"✅ Usunięto {deleted_total} legacy MENTIONS relationships")
        logger.info("ℹ️  RAG MENTIONS (Document → nodes) pozostały nietknięte")

    def delete_concept_nodes(self):
        """
        Usuwa wszystkie Concept nodes (wraz z ich relationships).
        """
        if self.dry_run:
            logger.info("[DRY-RUN] Usuwanie Concept nodes...")
            return

        logger.info("🗑️  Usuwanie Concept nodes...")

        with self.driver.session() as session:
            # DETACH DELETE usuwa node wraz z wszystkimi relationships
            result = session.run("""
                MATCH (n:Concept)
                DETACH DELETE n
                RETURN count(n) as deleted
            """)

            deleted = result.single()['deleted']

        logger.info(f"✅ Usunięto {deleted} Concept nodes")

    def delete_emotion_nodes(self):
        """
        Usuwa wszystkie Emotion nodes (wraz z ich relationships).
        """
        if self.dry_run:
            logger.info("[DRY-RUN] Usuwanie Emotion nodes...")
            return

        logger.info("🗑️  Usuwanie Emotion nodes...")

        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Emotion)
                DETACH DELETE n
                RETURN count(n) as deleted
            """)

            deleted = result.single()['deleted']

        logger.info(f"✅ Usunięto {deleted} Emotion nodes")

    def delete_unused_persona_nodes(self):
        """
        Usuwa Persona nodes które NIE mają doc_id (nie są używane przez personas table).
        """
        if self.dry_run:
            logger.info("[DRY-RUN] Usuwanie unused Persona nodes...")
            return

        logger.info("🗑️  Usuwanie unused Persona nodes (bez doc_id)...")

        with self.driver.session() as session:
            # Usuń tylko Persona nodes bez doc_id
            result = session.run("""
                MATCH (n:Persona)
                WHERE n.doc_id IS NULL
                DETACH DELETE n
                RETURN count(n) as deleted
            """)

            deleted = result.single()['deleted']

        logger.info(f"✅ Usunięto {deleted} unused Persona nodes")

    def get_post_cleanup_stats(self) -> Dict[str, Any]:
        """
        Zbiera statystyki PO cleanup (weryfikacja).

        Returns:
            Dict ze statystykami
        """
        logger.info("📊 Zbieranie statystyk POST-CLEANUP...")

        with self.driver.session() as session:
            # 1. Total counts
            result = session.run("MATCH (n) RETURN count(n) as count")
            total_nodes = result.single()['count']

            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_rels = result.single()['count']

            # 2. Legacy MENTIONS (should be 0 for Persona -> Concept)
            result = session.run("MATCH (p:Persona)-[r:MENTIONS]->(c:Concept) RETURN count(r) as count")
            legacy_mentions_count = result.single()['count']

            # RAG MENTIONS (should remain unchanged)
            result = session.run("""
                MATCH (d:Document)-[r:MENTIONS]->(n)
                WHERE n:Wskaznik OR n:Obserwacja OR n:Trend OR n:Demografia OR n:Lokalizacja
                RETURN count(r) as count
            """)
            rag_mentions_count = result.single()['count']

            result = session.run("MATCH (n:Concept) RETURN count(n) as count")
            concept_count = result.single()['count']

            result = session.run("MATCH (n:Emotion) RETURN count(n) as count")
            emotion_count = result.single()['count']

            result = session.run("""
                MATCH (n:Persona)
                WHERE n.doc_id IS NULL
                RETURN count(n) as count
            """)
            unused_persona_count = result.single()['count']

            # 3. RAG nodes (verify intact)
            rag_node_types = ['Wskaznik', 'Obserwacja', 'Trend', 'Demografia', 'Lokalizacja', 'RAGChunk']
            rag_counts = {}
            for node_type in rag_node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                rag_counts[node_type] = result.single()['count']

            # 4. RAG relationships (verify intact)
            rag_rel_types = ['OPISUJE', 'DOTYCZY', 'POKAZUJE_TREND', 'ZLOKALIZOWANY_W', 'POWIAZANY_Z']
            rag_rel_counts = {}
            for rel_type in rag_rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                rag_rel_counts[rel_type] = result.single()['count']

            stats = {
                'total_nodes': total_nodes,
                'total_rels': total_rels,
                'legacy_mentions_count': legacy_mentions_count,
                'rag_mentions_count': rag_mentions_count,
                'concept_count': concept_count,
                'emotion_count': emotion_count,
                'unused_persona_count': unused_persona_count,
                'rag_node_counts': rag_counts,
                'rag_rel_counts': rag_rel_counts
            }

            return stats

    def verify_cleanup(self, pre_stats: Dict[str, Any], post_stats: Dict[str, Any]) -> bool:
        """
        Weryfikuje że cleanup się powiódł.

        Args:
            pre_stats: Statystyki przed cleanup
            post_stats: Statystyki po cleanup

        Returns:
            True jeśli weryfikacja pomyślna
        """
        logger.info("🔍 Weryfikacja cleanup...")

        success = True

        # 1. Verify legacy MENTIONS deleted
        if post_stats['legacy_mentions_count'] != 0:
            logger.error(f"❌ Legacy MENTIONS count: {post_stats['legacy_mentions_count']} (expected 0)")
            success = False
        else:
            logger.info("✅ Legacy MENTIONS (Persona → Concept) count: 0")

        # Verify RAG MENTIONS intact
        if pre_stats.get('rag_mentions_count', 0) != post_stats.get('rag_mentions_count', 0):
            logger.error(f"❌ RAG MENTIONS changed: {pre_stats.get('rag_mentions_count', 0)} → {post_stats.get('rag_mentions_count', 0)}")
            success = False
        else:
            if post_stats.get('rag_mentions_count', 0) > 0:
                logger.info(f"✅ RAG MENTIONS (Document → nodes) intact: {post_stats.get('rag_mentions_count', 0)}")

        if post_stats['concept_count'] != 0:
            logger.error(f"❌ Concept count: {post_stats['concept_count']} (expected 0)")
            success = False
        else:
            logger.info("✅ Concept count: 0")

        if post_stats['emotion_count'] != 0:
            logger.error(f"❌ Emotion count: {post_stats['emotion_count']} (expected 0)")
            success = False
        else:
            logger.info("✅ Emotion count: 0")

        if post_stats['unused_persona_count'] != 0:
            logger.error(f"❌ Unused Persona count: {post_stats['unused_persona_count']} (expected 0)")
            success = False
        else:
            logger.info("✅ Unused Persona count: 0")

        # 2. Verify RAG nodes intact
        for node_type, pre_count in pre_stats['rag_node_counts'].items():
            post_count = post_stats['rag_node_counts'][node_type]

            if pre_count != post_count:
                logger.error(f"❌ {node_type} nodes changed: {pre_count} -> {post_count}")
                success = False
            else:
                if pre_count > 0:
                    logger.info(f"✅ {node_type} nodes intact: {post_count}")

        # 3. Verify RAG relationships intact
        for rel_type, pre_count in pre_stats['rag_rel_counts'].items():
            post_count = post_stats['rag_rel_counts'][rel_type]

            if pre_count != post_count:
                logger.error(f"❌ {rel_type} relationships changed: {pre_count} -> {post_count}")
                success = False
            else:
                if pre_count > 0:
                    logger.info(f"✅ {rel_type} relationships intact: {post_count}")

        return success

    def print_post_cleanup_summary(
        self,
        pre_stats: Dict[str, Any],
        post_stats: Dict[str, Any]
    ):
        """
        Wyświetla podsumowanie cleanup (przed/po porównanie).

        Args:
            pre_stats: Statystyki przed cleanup
            post_stats: Statystyki po cleanup
        """
        print()
        print("=" * 80)
        print("POST-CLEANUP SUMMARY")
        print("=" * 80)
        print()

        print("-" * 80)
        print("BEFORE → AFTER")
        print("-" * 80)

        print(f"Total Nodes: {pre_stats['total_nodes']} → {post_stats['total_nodes']} "
              f"({post_stats['total_nodes'] - pre_stats['total_nodes']:+d})")

        print(f"Total Relationships: {pre_stats['total_rels']} → {post_stats['total_rels']} "
              f"({post_stats['total_rels'] - pre_stats['total_rels']:+d})")

        print()

        print("-" * 80)
        print("LEGACY DATA DELETED")
        print("-" * 80)

        print(f"Legacy MENTIONS (Persona → Concept): {pre_stats['legacy_mentions_count']} → {post_stats['legacy_mentions_count']}")
        print(f"Concept nodes: {pre_stats['concept_count']} → {post_stats['concept_count']}")
        print(f"Emotion nodes: {pre_stats['emotion_count']} → {post_stats['emotion_count']}")
        print(f"Unused Persona nodes: {pre_stats['persona_without_doc_id']} → {post_stats['unused_persona_count']}")

        print()

        total_deleted = (
            pre_stats['legacy_mentions_count'] +
            pre_stats['concept_count'] +
            pre_stats['emotion_count'] +
            pre_stats['persona_without_doc_id']
        )

        print(f"✅ TOTAL DELETED: {total_deleted} legacy items")
        print()

        print("-" * 80)
        print("RAG DATA PRESERVED")
        print("-" * 80)

        print(f"RAG MENTIONS (Document → nodes): {pre_stats['rag_mentions_count']} → {post_stats['rag_mentions_count']} (unchanged)")
        print(f"  ℹ️  RAG relationships pozostały nietknięte")
        print()

    def close(self):
        """Zamyka połączenie z Neo4j."""
        if self.driver:
            self.driver.close()


def main():
    """Main cleanup workflow."""
    parser = argparse.ArgumentParser(
        description="Cleanup legacy MENTIONS data z Neo4j"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Tylko sprawdź co zostanie usunięte bez wykonywania cleanup'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("LEGACY MENTIONS CLEANUP")
    print("=" * 80)
    print()

    if args.dry_run:
        print("⚠️  DRY-RUN MODE: Żadne zmiany nie zostaną wykonane")
        print()

    # Initialize cleanup manager
    cleanup = LegacyCleanup(dry_run=args.dry_run)

    # Connect to Neo4j
    if not cleanup.connect():
        sys.exit(1)

    try:
        # 1. PRE-CLEANUP STATS
        print()
        print("-" * 80)
        print("STEP 1: PRE-CLEANUP VERIFICATION")
        print("-" * 80)
        print()

        pre_stats = cleanup.get_pre_cleanup_stats()
        cleanup.print_pre_cleanup_summary(pre_stats)

        # Check if there's anything to clean
        total_legacy = (
            pre_stats['legacy_mentions_count'] +
            pre_stats['concept_count'] +
            pre_stats['emotion_count'] +
            pre_stats['persona_without_doc_id']
        )

        if total_legacy == 0:
            print("✅ Brak legacy data do usunięcia - graf jest czysty!")
            print()
            sys.exit(0)

        # 2. CHECK DEPENDENCIES
        print()
        print("-" * 80)
        print("STEP 2: DEPENDENCY CHECK")
        print("-" * 80)
        print()

        if not cleanup.check_dependencies():
            logger.error("❌ Wykryto nieoczekiwane dependencies - zatrzymuję cleanup")
            logger.error("Przejrzyj logi i ręcznie sprawdź graf przed cleanup")
            sys.exit(1)

        print()

        # 3. CONFIRMATION (jeśli nie dry-run)
        if not args.dry_run:
            print()
            print("=" * 80)
            print("⚠️  UWAGA: TO JEST OPERACJA DESTRUKCYJNA")
            print("=" * 80)
            print()
            print(f"Zamierzasz usunąć {total_legacy} items z grafu Neo4j.")
            print()
            print("Upewnij się że:")
            print("  1. Masz backup: python scripts/backup_neo4j.py")
            print("  2. Przejrzałeś powyższe statystyki")
            print("  3. Jesteś pewien że chcesz kontynuować")
            print()

            confirmation = input("Czy kontynuować cleanup? (wpisz 'YES' aby kontynuować): ")

            if confirmation != "YES":
                print()
                print("Cleanup anulowany przez użytkownika")
                sys.exit(0)

            print()

        # 4. CLEANUP OPERATIONS
        print()
        print("-" * 80)
        print("STEP 3: CLEANUP OPERATIONS")
        print("-" * 80)
        print()

        cleanup.delete_mentions_relationships()
        cleanup.delete_concept_nodes()
        cleanup.delete_emotion_nodes()
        cleanup.delete_unused_persona_nodes()

        print()

        if args.dry_run:
            print("=" * 80)
            print("DRY-RUN COMPLETED")
            print("=" * 80)
            print()
            print("✅ Żadne zmiany nie zostały wykonane (--dry-run mode)")
            print()
            print("Aby wykonać właściwy cleanup:")
            print("  1. Najpierw zrób backup: python scripts/backup_neo4j.py")
            print("  2. Uruchom cleanup: python scripts/cleanup_legacy_mentions.py")
            print()
            sys.exit(0)

        # 5. POST-CLEANUP VERIFICATION
        print()
        print("-" * 80)
        print("STEP 4: POST-CLEANUP VERIFICATION")
        print("-" * 80)
        print()

        post_stats = cleanup.get_post_cleanup_stats()

        if not cleanup.verify_cleanup(pre_stats, post_stats):
            logger.error("❌ Weryfikacja cleanup FAILED")
            logger.error("Sprawdź logi powyżej i rozważ rollback z backup")
            sys.exit(1)

        # 6. SUMMARY
        cleanup.print_post_cleanup_summary(pre_stats, post_stats)

        print()
        print("=" * 80)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("Graf Neo4j został wyczyszczony z legacy data.")
        print()
        print("Jeśli coś poszło nie tak, przywróć backup:")
        print("  1. Zatrzymaj aplikację: docker-compose down")
        print("  2. Usuń Neo4j volume: docker volume rm market-research-saas_neo4j_data")
        print("  3. Uruchom Neo4j: docker-compose up -d neo4j")
        print("  4. Załaduj backup: cypher-shell < data/backups/neo4j-backup-TIMESTAMP.cypher")
        print()

    except Exception as e:
        logger.error(f"❌ BŁĄD podczas cleanup: {e}", exc_info=True)
        sys.exit(1)

    finally:
        cleanup.close()


if __name__ == "__main__":
    main()
