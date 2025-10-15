#!/usr/bin/env python3
"""
Inicjalizacja Neo4j Indexes dla RAG System

Tworzy wymagane indeksy:
1. Vector index dla semantic search (rag_document_embeddings)
2. Fulltext index dla keyword search (rag_fulltext_index)

Uruchomienie:
    python scripts/init_neo4j_indexes.py

Wymaga:
    - Uruchomiony Neo4j (docker-compose up neo4j)
    - Poprawne NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD w .env

WAŻNE: Script jest idempotentny (sprawdza IF NOT EXISTS) i non-fatal
       (zwraca exit code 0 nawet jeśli Neo4j niedostępny).
       Jest używany w docker-entrypoint.sh dla automatycznej inicjalizacji.
"""

import sys
import time
from pathlib import Path

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()

# Konfiguracja dla Docker environment
MAX_RETRIES = 3  # Krótszy retry bo entrypoint już czeka na Neo4j
RETRY_DELAY = 2.0  # 2s między próbami


def init_neo4j_indexes():
    """
    Inicjalizuj wszystkie wymagane indeksy w Neo4j

    Returns:
        bool: True jeśli sukces, False jeśli failed (ale nie rzuca exception)
    """
    print("=" * 80)
    print("NEO4J INDEXES INITIALIZATION (Docker Environment)")
    print("=" * 80)
    print()

    print(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

    driver = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=30,  # Short timeout dla Docker startup
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
                print()
                print("This is NON-FATAL - RAG services have their own retry logic.")
                print("API will start, but RAG features may be unavailable until Neo4j is ready.")
                return False

    if not driver:
        return False

    # Create indexes
    try:
        with driver.session() as session:

            # 1. Vector Index for Semantic Search
            print("-" * 80)
            print("1. VECTOR INDEX (semantic search)")
            print("-" * 80)

            try:
                # Check if index exists
                result = session.run("SHOW INDEXES")
                existing_indexes = [record["name"] for record in result]

                if "rag_document_embeddings" in existing_indexes:
                    print("ℹ️  Vector index 'rag_document_embeddings' already exists (SKIP)")

                    # Show index details (for debugging)
                    result = session.run("""
                        SHOW INDEXES
                        YIELD name, labelsOrTypes, properties, type, state
                        WHERE name = 'rag_document_embeddings'
                        RETURN name, labelsOrTypes, properties, type, state
                    """)
                    for record in result:
                        print(f"   State: {record['state']}")
                else:
                    print("Creating vector index 'rag_document_embeddings'...")

                    # Create vector index
                    # Syntax for Neo4j 5.x+
                    session.run("""
                        CREATE VECTOR INDEX rag_document_embeddings IF NOT EXISTS
                        FOR (n:RAGChunk)
                        ON n.embedding
                        OPTIONS {
                            indexConfig: {
                                `vector.dimensions`: 3072,
                                `vector.similarity_function`: 'cosine'
                            }
                        }
                    """)

                    print("✅ Vector index created successfully")
                    print("   Index: rag_document_embeddings")
                    print("   Node: RAGChunk")
                    print("   Property: embedding")
                    print("   Dimensions: 3072 (Google Gemini gemini-embedding-001)")
                    print("   Similarity: cosine")

            except Exception as e:
                print(f"❌ ERROR creating vector index: {e}")
                print()
                print("If you see 'unsupported feature', make sure Neo4j version is 5.x+")
                print("Check: docker-compose.yml → neo4j image version")
                driver.close()
                return False

            print()

            # 2. Fulltext Index for Keyword Search
            print("-" * 80)
            print("2. FULLTEXT INDEX (keyword search)")
            print("-" * 80)

            try:
                # Check if index exists
                result = session.run("SHOW INDEXES")
                existing_indexes = [record["name"] for record in result]

                if "rag_fulltext_index" in existing_indexes:
                    print("ℹ️  Fulltext index 'rag_fulltext_index' already exists (SKIP)")

                    # Show index details
                    result = session.run("""
                        SHOW INDEXES
                        YIELD name, labelsOrTypes, properties, type, state
                        WHERE name = 'rag_fulltext_index'
                        RETURN name, labelsOrTypes, properties, type, state
                    """)
                    for record in result:
                        print(f"   State: {record['state']}")
                else:
                    print("Creating fulltext index 'rag_fulltext_index'...")

                    # Create fulltext index
                    session.run("""
                        CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
                        FOR (n:RAGChunk)
                        ON EACH [n.text]
                    """)

                    print("✅ Fulltext index created successfully")
                    print("   Index: rag_fulltext_index")
                    print("   Node: RAGChunk")
                    print("   Property: text")
                    print("   Type: fulltext (Lucene-based)")

            except Exception as e:
                print(f"❌ ERROR creating fulltext index: {e}")
                driver.close()
                return False

            print()

            # 3. Summary
            print("=" * 80)
            print("SUMMARY")
            print("=" * 80)

            # List all RAG-related indexes
            result = session.run("""
                SHOW INDEXES
                YIELD name, labelsOrTypes, properties, type, state
                WHERE name STARTS WITH 'rag'
                RETURN name, labelsOrTypes, properties, type, state
                ORDER BY name
            """)

            indexes = list(result)
            print(f"Found {len(indexes)} RAG indexes:")
            print()

            for record in indexes:
                status = "✅" if record['state'] == 'ONLINE' else "⚠️"
                print(f"{status} {record['name']} ({record['type']}) - {record['state']}")

            # Check if there are any RAGChunk nodes
            result = session.run("MATCH (n:RAGChunk) RETURN count(n) as count")
            chunk_count = result.single()['count']

            if chunk_count > 0:
                print(f"\n📊 Database contains {chunk_count} RAGChunk nodes")
            else:
                print("\nℹ️  Database is empty (no RAGChunk nodes yet)")
                print("   Upload documents via: POST /api/v1/rag/documents/upload")

            print()
            print("=" * 80)
            print("✅ NEO4J INDEXES INITIALIZED SUCCESSFULLY")
            print("=" * 80)
            print()

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        driver.close()
        return False

    finally:
        if driver:
            driver.close()

    return True


if __name__ == "__main__":
    success = init_neo4j_indexes()
    # WAŻNE: Zawsze zwracaj exit code 0 (non-fatal dla entrypoint)
    # RAG services mają własny retry logic, więc API może startować nawet jeśli indexes failed
    sys.exit(0)
