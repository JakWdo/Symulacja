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
from config import app as app_config, models as config_models

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

    print(f"Connecting to Neo4j at {app_config.neo4j.uri}...")

    driver = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = GraphDatabase.driver(
                app_config.neo4j.uri,
                auth=(app_config.neo4j.user, app_config.neo4j.password),
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
                # Determine embedding model and dimension (for vector index)
                embedding_model = config_models.get("rag", "embedding").model
                # Basic mapping for known providers; default to 768
                if "gemini-embedding" in embedding_model or "text-embedding-004" in embedding_model:
                    embedding_dimension = 768
                else:
                    embedding_dimension = 768
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
                    session.run(
                        f"""
                        CREATE VECTOR INDEX rag_document_embeddings IF NOT EXISTS
                        FOR (n:RAGChunk)
                        ON n.embedding
                        OPTIONS {{
                            indexConfig: {{
                                `vector.dimensions`: {embedding_dimension},
                                `vector.similarity_function`: 'cosine'
                            }}
                        }}
                    """
                    )

                    print("✅ Vector index created successfully")
                    print("   Index: rag_document_embeddings")
                    print("   Node: RAGChunk")
                    print("   Property: embedding")
                    print(f"   Dimensions: {embedding_dimension} (model: {embedding_model})")
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

            # 3. TEXT INDEXES for Graph RAG (streszczenie, kluczowe_fakty)
            print("-" * 80)
            print("3. TEXT INDEXES (Graph RAG performance optimization)")
            print("-" * 80)
            print("Creating TEXT indexes for CONTAINS queries on graph nodes...")
            print()

            # TEXT indexes dla przyspieszenia CONTAINS queries w Cypher
            # Neo4j 5.x+ wspiera TEXT INDEX dla string properties
            text_indexes = [
                # Wskaznik nodes
                ("wskaznik_streszczenie_text", "Wskaznik", "streszczenie"),
                ("wskaznik_fakty_text", "Wskaznik", "kluczowe_fakty"),
                # Obserwacja nodes
                ("obserwacja_streszczenie_text", "Obserwacja", "streszczenie"),
                ("obserwacja_fakty_text", "Obserwacja", "kluczowe_fakty"),
                # Trend nodes
                ("trend_streszczenie_text", "Trend", "streszczenie"),
                ("trend_fakty_text", "Trend", "kluczowe_fakty"),
                # Demografia nodes
                ("demografia_streszczenie_text", "Demografia", "streszczenie"),
                ("demografia_fakty_text", "Demografia", "kluczowe_fakty"),
            ]

            created_count = 0
            skipped_count = 0

            for index_name, node_label, property_name in text_indexes:
                try:
                    # Check if index exists
                    result = session.run("SHOW INDEXES")
                    existing_indexes = [record["name"] for record in result]

                    if index_name in existing_indexes:
                        print(f"   ℹ️  TEXT index '{index_name}' already exists (SKIP)")
                        skipped_count += 1
                    else:
                        # Create TEXT index
                        # Neo4j 5.x+ syntax
                        session.run(f"""
                            CREATE TEXT INDEX {index_name} IF NOT EXISTS
                            FOR (n:{node_label})
                            ON (n.{property_name})
                        """)
                        print(f"   ✅ Created TEXT index '{index_name}' on {node_label}.{property_name}")
                        created_count += 1

                except Exception as e:
                    print(f"   ⚠️  ERROR creating TEXT index '{index_name}': {e}")
                    # Continue with other indexes (non-fatal)

            print()
            print(f"TEXT indexes: {created_count} created, {skipped_count} skipped")
            print("These indexes speed up CONTAINS queries in get_demographic_graph_context()")

            print()

            # 4. Summary
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
