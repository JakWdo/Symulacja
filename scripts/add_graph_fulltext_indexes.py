#!/usr/bin/env python3
"""
Dodaj fulltext indeksy dla Graph RAG nodes

PROBLEM:
- get_demographic_graph_context() używa CONTAINS na streszczenie/kluczowe_fakty
- Bez fulltext indeksów → full table scan → 10-30s query time → timeouty
- Logi: "⚠️ Graph RAG queries przekroczyły timeout (30s)"

ROZWIĄZANIE:
- Fulltext index na (Wskaznik|Obserwacja|Trend|Demografia) nodes
- Properties: [streszczenie, kluczowe_fakty]
- CONTAINS → db.index.fulltext.queryNodes() (przyspieszenie 60x+)

Uruchomienie:
    python scripts/add_graph_fulltext_indexes.py

WAŻNE: Script jest idempotentny (sprawdza IF NOT EXISTS)
"""

import sys
import time
from pathlib import Path

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()

MAX_RETRIES = 5
RETRY_DELAY = 3.0


def add_graph_fulltext_indexes():
    """
    Dodaj fulltext indeksy dla Graph RAG demographic nodes

    Tworzy indeksy:
    1. graph_demographic_fulltext - dla wszystkich typów demographic nodes

    Returns:
        bool: True jeśli sukces, False jeśli failed
    """
    print("=" * 80)
    print("ADD GRAPH FULLTEXT INDEXES")
    print("=" * 80)
    print()
    print("Problem: GraphRAG queries timeoutują (CONTAINS bez indeksów)")
    print("Solution: Fulltext index dla (Wskaznik|Obserwacja|Trend|Demografia)")
    print()

    print(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

    driver = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=30,
            )

            # Test connection
            driver.verify_connectivity()
            print(f"✅ Connected to Neo4j successfully (attempt {attempt}/{MAX_RETRIES})")
            print()
            break

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"⚠️  Connection attempt {attempt}/{MAX_RETRIES} failed: {str(e)[:100]}")
                print(f"   Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ ERROR: Could not connect to Neo4j after {MAX_RETRIES} attempts")
                print(f"   Last error: {e}")
                return False

    if not driver:
        return False

    try:
        with driver.session() as session:

            # Check existing indexes
            print("-" * 80)
            print("CHECKING EXISTING INDEXES")
            print("-" * 80)

            result = session.run("SHOW INDEXES")
            existing_indexes = [record["name"] for record in result]

            print(f"Found {len(existing_indexes)} total indexes in database")
            graph_indexes = [idx for idx in existing_indexes if 'graph' in idx.lower()]
            if graph_indexes:
                print(f"Existing graph indexes: {', '.join(graph_indexes)}")
            else:
                print("No graph-related indexes found")

            print()

            # 1. Fulltext Index for Graph Demographic Nodes
            print("-" * 80)
            print("FULLTEXT INDEX: graph_demographic_fulltext")
            print("-" * 80)

            index_name = "graph_demographic_fulltext"

            if index_name in existing_indexes:
                print(f"ℹ️  Index '{index_name}' already exists (SKIP)")

                # Show index details
                result = session.run("""
                    SHOW INDEXES
                    YIELD name, labelsOrTypes, properties, type, state
                    WHERE name = $index_name
                    RETURN name, labelsOrTypes, properties, type, state
                """, index_name=index_name)

                for record in result:
                    print(f"   State: {record['state']}")
                    print(f"   Labels: {record['labelsOrTypes']}")
                    print(f"   Properties: {record['properties']}")

            else:
                print(f"Creating fulltext index '{index_name}'...")
                print()
                print("Target nodes: Wskaznik, Obserwacja, Trend, Demografia")
                print("Properties: streszczenie, kluczowe_fakty")
                print()

                # Create fulltext index for all demographic node types
                # Note: Neo4j fulltext index syntax allows multiple labels
                session.run(f"""
                    CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
                    FOR (n:Wskaznik|Obserwacja|Trend|Demografia)
                    ON EACH [n.streszczenie, n.kluczowe_fakty]
                """)

                print(f"✅ Index '{index_name}' created successfully")
                print()
                print("⏳ Index is being populated in background...")
                print("   State will change: POPULATING → ONLINE")
                print("   Check status: SHOW INDEXES WHERE name = 'graph_demographic_fulltext'")

            print()

            # Summary - show all indexes
            print("=" * 80)
            print("SUMMARY")
            print("=" * 80)

            result = session.run("""
                SHOW INDEXES
                YIELD name, labelsOrTypes, properties, type, state
                WHERE name STARTS WITH 'rag' OR name STARTS WITH 'graph'
                RETURN name, labelsOrTypes, properties, type, state
                ORDER BY name
            """)

            indexes = list(result)
            print(f"Found {len(indexes)} RAG/Graph indexes:")
            print()

            for record in indexes:
                status = "✅" if record['state'] == 'ONLINE' else "⚠️ "
                print(f"{status} {record['name']} ({record['type']}) - {record['state']}")
                print(f"   Labels: {record['labelsOrTypes']}")
                print(f"   Properties: {record['properties']}")
                print()

            # Count demographic nodes by type
            print("-" * 80)
            print("DEMOGRAPHIC NODES COUNT")
            print("-" * 80)

            for node_type in ['Wskaznik', 'Obserwacja', 'Trend', 'Demografia']:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                count = result.single()['count']

                if count > 0:
                    print(f"📊 {node_type}: {count} nodes")
                else:
                    print(f"ℹ️  {node_type}: 0 nodes (empty)")

            print()
            print("=" * 80)
            print("✅ GRAPH FULLTEXT INDEXES INITIALIZED SUCCESSFULLY")
            print("=" * 80)
            print()
            print("NEXT STEPS:")
            print("1. Update get_demographic_graph_context() to use fulltext search")
            print("2. Replace CONTAINS → db.index.fulltext.queryNodes()")
            print("3. Expected performance: 10-30s → <500ms")
            print()

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        driver.close()
        return False

    finally:
        if driver:
            driver.close()

    return True


if __name__ == "__main__":
    success = add_graph_fulltext_indexes()
    sys.exit(0 if success else 1)
