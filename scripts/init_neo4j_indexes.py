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
"""

import sys
from pathlib import Path

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()


def init_neo4j_indexes():
    """
    Inicjalizuj wszystkie wymagane indeksy w Neo4j
    """
    print("=" * 80)
    print("NEO4J INDEXES INITIALIZATION")
    print("=" * 80)
    print()

    print(f"Connecting to Neo4j at {settings.NEO4J_URI}...")

    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        # Test connection
        driver.verify_connectivity()
        print("✅ Connected to Neo4j successfully")
        print()

    except Exception as e:
        print(f"❌ ERROR: Could not connect to Neo4j: {e}")
        print()
        print("Make sure:")
        print("  1. Neo4j is running: docker-compose up -d neo4j")
        print("  2. NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD are correct in .env")
        return False

    # Create indexes
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
                print("ℹ️  Vector index 'rag_document_embeddings' already exists")

                # Show index details
                result = session.run("""
                    SHOW INDEXES
                    YIELD name, labelsOrTypes, properties, type, state
                    WHERE name = 'rag_document_embeddings'
                    RETURN name, labelsOrTypes, properties, type, state
                """)
                for record in result:
                    print(f"   Name: {record['name']}")
                    print(f"   Labels: {record['labelsOrTypes']}")
                    print(f"   Properties: {record['properties']}")
                    print(f"   Type: {record['type']}")
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
                            `vector.dimensions`: 768,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """)

                print("✅ Vector index created successfully")
                print("   Index: rag_document_embeddings")
                print("   Node: RAGChunk")
                print("   Property: embedding")
                print("   Dimensions: 768 (Google Gemini text-embedding-004)")
                print("   Similarity: cosine")

        except Exception as e:
            print(f"❌ ERROR creating vector index: {e}")
            print()
            print("If you see 'unsupported feature' error, make sure you're using Neo4j 5.x+")
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
                print("ℹ️  Fulltext index 'rag_fulltext_index' already exists")

                # Show index details
                result = session.run("""
                    SHOW INDEXES
                    YIELD name, labelsOrTypes, properties, type, state
                    WHERE name = 'rag_fulltext_index'
                    RETURN name, labelsOrTypes, properties, type, state
                """)
                for record in result:
                    print(f"   Name: {record['name']}")
                    print(f"   Labels: {record['labelsOrTypes']}")
                    print(f"   Properties: {record['properties']}")
                    print(f"   Type: {record['type']}")
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
            print(f"{status} {record['name']}")
            print(f"   Labels: {record['labelsOrTypes']}")
            print(f"   Properties: {record['properties']}")
            print(f"   Type: {record['type']}")
            print(f"   State: {record['state']}")
            print()

        # Check if there are any RAGChunk nodes
        result = session.run("MATCH (n:RAGChunk) RETURN count(n) as count")
        chunk_count = result.single()['count']

        if chunk_count > 0:
            print(f"📊 Database contains {chunk_count} RAGChunk nodes")
        else:
            print("ℹ️  Database is empty (no RAGChunk nodes yet)")
            print("   Upload documents via: POST /api/v1/rag/documents/upload")

        print()
        print("=" * 80)
        print("✅ NEO4J INDEXES INITIALIZED SUCCESSFULLY")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Upload RAG documents: POST /api/v1/rag/documents/upload")
        print("  2. Test hybrid search: python scripts/test_hybrid_search.py")
        print("  3. Generate personas: POST /api/v1/projects/{id}/personas/generate")
        print()

    driver.close()
    return True


if __name__ == "__main__":
    success = init_neo4j_indexes()
    sys.exit(0 if success else 1)
