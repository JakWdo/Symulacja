#!/usr/bin/env python3
"""
Neo4j Backup Script

Tworzy backup grafu Neo4j do pliku .cypher (Cypher statements).

Funkcjonalności:
- Eksport wszystkich nodes i relationships do Cypher statements
- Weryfikacja połączenia z Neo4j przed backup
- Tworzenie timestamped backups w data/backups/
- --dry-run mode (sprawdza co zostanie zrobione bez tworzenia backup)
- Weryfikacja że backup się powiódł

Uruchomienie:
    python scripts/backup_neo4j.py                    # Normalny backup
    python scripts/backup_neo4j.py --dry-run          # Podgląd bez tworzenia backup
    python scripts/backup_neo4j.py --output custom.cypher  # Custom output path

Wymaga:
    - Uruchomiony Neo4j (docker-compose up neo4j)
    - Poprawne NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD w .env
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()


class Neo4jBackup:
    """
    Neo4j Backup Manager

    Attributes:
        driver: Neo4j driver instance
        backup_dir: Ścieżka do katalogu z backupami
    """

    def __init__(self):
        """Inicjalizuje backup manager i tworzy katalog backups."""
        self.driver = None
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """
        Nawiązuje połączenie z Neo4j.

        Returns:
            True jeśli połączenie udane, False w przeciwnym razie
        """
        print(f"🔌 Łączę się z Neo4j: {settings.NEO4J_URI}")

        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            # Weryfikuj połączenie
            self.driver.verify_connectivity()
            print("✅ Połączono z Neo4j pomyślnie\n")
            return True

        except Exception as e:
            print(f"❌ BŁĄD: Nie można połączyć się z Neo4j: {e}\n")
            print("Upewnij się że:")
            print("  1. Neo4j jest uruchomiony: docker-compose up -d neo4j")
            print("  2. NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD są poprawne w .env")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Pobiera statystyki bazy danych.

        Returns:
            Dict z counts nodes, relationships, labels, relationship types
        """
        with self.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']

            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']

            # Get all labels
            result = session.run("CALL db.labels()")
            labels = [record['label'] for record in result]

            # Get all relationship types
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record['relationshipType'] for record in result]

            return {
                'node_count': node_count,
                'rel_count': rel_count,
                'labels': labels,
                'rel_types': rel_types
            }

    def export_to_cypher(self) -> List[str]:
        """
        Eksportuje cały graf do Cypher statements.

        Returns:
            Lista stringów z Cypher statements (CREATE statements)
        """
        statements = []

        with self.driver.session() as session:
            # 1. Export nodes
            # Pobierz wszystkie labels
            result = session.run("CALL db.labels()")
            labels = [record['label'] for record in result]

            print(f"📦 Eksportuję nodes dla {len(labels)} labels...")

            for label in labels:
                # Pobierz nodes dla tego label
                result = session.run(f"MATCH (n:{label}) RETURN n")

                for record in result:
                    node = record['n']
                    node_id = node.id
                    node_labels = ':'.join(node.labels)

                    # Serialize properties
                    props = dict(node.items())

                    # Utwórz CREATE statement
                    # Format: CREATE (n:Label {prop1: value1, prop2: value2})
                    props_str = self._serialize_properties(props)

                    statement = f"CREATE (n{node_id}:{node_labels} {props_str});"
                    statements.append(statement)

            # 2. Export relationships
            print(f"🔗 Eksportuję relationships...")

            result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b")

            for record in result:
                source = record['a']
                rel = record['r']
                target = record['b']

                source_id = source.id
                target_id = target.id
                rel_type = rel.type

                # Serialize relationship properties
                rel_props = dict(rel.items())
                rel_props_str = self._serialize_properties(rel_props)

                if rel_props_str != "{}":
                    statement = f"MATCH (a), (b) WHERE id(a)={source_id} AND id(b)={target_id} CREATE (a)-[r:{rel_type} {rel_props_str}]->(b);"
                else:
                    statement = f"MATCH (a), (b) WHERE id(a)={source_id} AND id(b)={target_id} CREATE (a)-[r:{rel_type}]->(b);"

                statements.append(statement)

        return statements

    def _serialize_properties(self, props: Dict[str, Any]) -> str:
        """
        Serializes properties do formatu Cypher.

        Args:
            props: Dict z properties node/relationship

        Returns:
            String w formacie {prop1: value1, prop2: value2}
        """
        if not props:
            return "{}"

        # Filter out embedding vectors (zbyt duże dla text backup)
        filtered_props = {k: v for k, v in props.items() if k != 'embedding'}

        if not filtered_props:
            return "{}"

        # Serialize każdą property
        prop_strs = []
        for key, value in filtered_props.items():
            # Escape strings
            if isinstance(value, str):
                # Escape single quotes i backslashes
                escaped = value.replace("\\", "\\\\").replace("'", "\\'")
                prop_strs.append(f"{key}: '{escaped}'")
            elif isinstance(value, bool):
                prop_strs.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                prop_strs.append(f"{key}: {value}")
            elif value is None:
                prop_strs.append(f"{key}: null")
            elif isinstance(value, list):
                # Serialize lists
                list_str = str(value).replace("'", '"')
                prop_strs.append(f"{key}: {list_str}")
            else:
                # Default: convert to string
                escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
                prop_strs.append(f"{key}: '{escaped}'")

        return "{" + ", ".join(prop_strs) + "}"

    def save_backup(self, statements: List[str], output_path: Path) -> bool:
        """
        Zapisuje backup do pliku.

        Args:
            statements: Lista Cypher statements
            output_path: Ścieżka do pliku output

        Returns:
            True jeśli backup zapisany pomyślnie
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("// Neo4j Backup\n")
                f.write(f"// Created: {datetime.now().isoformat()}\n")
                f.write(f"// Source: {settings.NEO4J_URI}\n")
                f.write("//\n")
                f.write("// UWAGA: Ten backup NIE zawiera embedding vectors (zbyt duże)\n")
                f.write("// Aby przywrócić embeddings, należy ponownie uruchomić RAG ingest\n")
                f.write("//\n\n")

                # Statements
                for statement in statements:
                    f.write(statement + "\n")

            print(f"✅ Backup zapisany do: {output_path}")
            print(f"   Rozmiar: {output_path.stat().st_size / 1024:.2f} KB")
            return True

        except Exception as e:
            print(f"❌ BŁĄD podczas zapisywania backup: {e}")
            return False

    def verify_backup(self, backup_path: Path, expected_count: int) -> bool:
        """
        Weryfikuje że backup się powiódł.

        Args:
            backup_path: Ścieżka do backup file
            expected_count: Oczekiwana liczba statements

        Returns:
            True jeśli weryfikacja pomyślna
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Count non-comment lines
            statement_count = sum(1 for line in lines if line.strip() and not line.strip().startswith('//'))

            if statement_count == expected_count:
                print(f"✅ Weryfikacja pomyślna: {statement_count} statements")
                return True
            else:
                print(f"⚠️  Ostrzeżenie: Zapisano {statement_count} statements, oczekiwano {expected_count}")
                return False

        except Exception as e:
            print(f"❌ BŁĄD podczas weryfikacji backup: {e}")
            return False

    def close(self):
        """Zamyka połączenie z Neo4j."""
        if self.driver:
            self.driver.close()


def main():
    """Main backup workflow."""
    parser = argparse.ArgumentParser(
        description="Backup Neo4j graph do Cypher statements"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Tylko sprawdź co zostanie zrobione bez tworzenia backup'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Custom output path (default: data/backups/neo4j-backup-TIMESTAMP.cypher)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("NEO4J BACKUP")
    print("=" * 80)
    print()

    # Initialize backup manager
    backup = Neo4jBackup()

    # Connect to Neo4j
    if not backup.connect():
        sys.exit(1)

    try:
        # Get database stats
        print("-" * 80)
        print("DATABASE STATS")
        print("-" * 80)

        stats = backup.get_database_stats()

        print(f"Nodes: {stats['node_count']}")
        print(f"Relationships: {stats['rel_count']}")
        print(f"Labels ({len(stats['labels'])}): {', '.join(stats['labels'])}")
        print(f"Relationship Types ({len(stats['rel_types'])}): {', '.join(stats['rel_types'])}")
        print()

        if stats['node_count'] == 0:
            print("⚠️  UWAGA: Baza danych jest pusta - backup nie zawiera danych")
            print()

        # Dry-run mode
        if args.dry_run:
            print("-" * 80)
            print("DRY-RUN MODE")
            print("-" * 80)
            print()
            print("✅ Backup NIE został utworzony (--dry-run mode)")
            print()
            print(f"W normalnym trybie zostałby utworzony backup zawierający:")
            print(f"  - {stats['node_count']} nodes")
            print(f"  - {stats['rel_count']} relationships")
            print(f"  - Razem: ~{stats['node_count'] + stats['rel_count']} Cypher statements")
            print()

            if args.output:
                print(f"Output path: {args.output}")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
                default_path = backup.backup_dir / f"neo4j-backup-{timestamp}.cypher"
                print(f"Output path: {default_path}")

            print()
            print("Aby utworzyć backup, uruchom bez --dry-run:")
            print(f"  python scripts/backup_neo4j.py")
            print()

            sys.exit(0)

        # Normal backup mode
        print("-" * 80)
        print("EXPORTING TO CYPHER")
        print("-" * 80)
        print()

        statements = backup.export_to_cypher()

        print()
        print(f"✅ Wyeksportowano {len(statements)} Cypher statements")
        print()

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
            output_path = backup.backup_dir / f"neo4j-backup-{timestamp}.cypher"

        # Save backup
        print("-" * 80)
        print("SAVING BACKUP")
        print("-" * 80)
        print()

        if not backup.save_backup(statements, output_path):
            sys.exit(1)

        # Verify backup
        print()
        print("-" * 80)
        print("VERIFICATION")
        print("-" * 80)
        print()

        if not backup.verify_backup(output_path, len(statements)):
            sys.exit(1)

        # Summary
        print()
        print("=" * 80)
        print("✅ BACKUP COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print(f"Backup location: {output_path}")
        print()
        print("Aby przywrócić backup:")
        print(f"  1. Zatrzymaj aplikację: docker-compose down")
        print(f"  2. Usuń Neo4j volume: docker volume rm sight_neo4j_data")
        print(f"  3. Uruchom Neo4j: docker-compose up -d neo4j")
        print(f"  4. Załaduj backup: cypher-shell < {output_path}")
        print(f"  5. Ponownie utwórz embeddings: POST /api/v1/rag/documents/upload")
        print()

    except Exception as e:
        print(f"❌ BŁĄD podczas backup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        backup.close()


if __name__ == "__main__":
    main()
