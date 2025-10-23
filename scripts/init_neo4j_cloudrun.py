#!/usr/bin/env python3
"""
Inicjalizacja Neo4j Indexes dla Cloud Run Deployment

Tworzy wszystkie wymagane indeksy dla RAG System:
1. Chunk indexes (vector + fulltext dla RAGChunk nodes) - CRITICAL
2. Graph indexes (fulltext dla demographic nodes) - PERFORMANCE

Wrapper dla init_neo4j_indexes.py + add_graph_fulltext_indexes.py z dodatkowymi features dla Cloud Run:
- Enhanced retry logic z exponential backoff
- Cloud Run Jobs specific error handling
- Healthcheck przed inicjalizacją
- Structured logging dla Cloud Logging
- Proper exit codes dla Cloud Run Jobs

Uruchomienie (Cloud Run Job):
    gcloud run jobs create neo4j-init \
      --image=IMAGE_URL \
      --command=python,scripts/init_neo4j_cloudrun.py \
      --set-secrets=NEO4J_URI=NEO4J_URI:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest \
      --set-env-vars=NEO4J_USER=neo4j

    gcloud run jobs execute neo4j-init --region=europe-central2 --wait

Wymaga:
    - Neo4j AuraDB running i dostępny
    - Secrets: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    - Połączenie sieciowe do Neo4j (firewall allow Cloud Run IPs)

Exit Codes:
    0 - Success (all indexes created or already exist)
    1 - Fatal error (Neo4j unreachable, chunk indexes failed)
    2 - Partial success (chunks OK, graph indexes failed - non-critical)
"""

import sys
import time
import logging
from pathlib import Path

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()

# Konfiguracja dla Cloud Run environment
MAX_RETRIES = 10  # Więcej retry dla Cloud Run (zewnętrzny Neo4j może być slow)
INITIAL_DELAY = 2.0  # Początkowe opóźnienie 2s
MAX_DELAY = 30.0  # Maksymalne opóźnienie 30s (exponential backoff)

# Cloud Logging structured format
logging.basicConfig(
    level=logging.INFO,
    format='{"severity":"%(levelname)s","message":"%(message)s","timestamp":"%(asctime)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
)
logger = logging.getLogger(__name__)


def log_structured(severity: str, message: str, **kwargs):
    """Log w formacie structured dla Cloud Logging."""
    log_data = {"severity": severity, "message": message, **kwargs}
    logger.log(
        getattr(logging, severity.upper(), logging.INFO),
        str(log_data)
    )


def test_neo4j_connectivity() -> bool:
    """
    Sprawdza czy Neo4j jest dostępny i można się uwierzytelnić.

    Returns:
        True jeśli Neo4j dostępny, False w przeciwnym razie
    """
    log_structured("INFO", "Testing Neo4j connectivity", uri=settings.NEO4J_URI)

    delay = INITIAL_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=10,
            )
            driver.verify_connectivity()
            driver.close()

            log_structured(
                "INFO",
                "Neo4j connectivity test successful",
                attempt=attempt,
                max_retries=MAX_RETRIES
            )
            return True

        except Exception as e:
            error_msg = str(e)[:200]  # Truncate long errors
            log_structured(
                "WARNING" if attempt < MAX_RETRIES else "ERROR",
                "Neo4j connectivity test failed",
                attempt=attempt,
                max_retries=MAX_RETRIES,
                error=error_msg,
                next_retry_delay=delay if attempt < MAX_RETRIES else None
            )

            if attempt < MAX_RETRIES:
                time.sleep(delay)
                # Exponential backoff
                delay = min(delay * 1.5, MAX_DELAY)
            else:
                log_structured(
                    "ERROR",
                    "Neo4j unreachable after all retries",
                    total_attempts=MAX_RETRIES,
                    total_time_seconds=int(sum(INITIAL_DELAY * (1.5 ** i) for i in range(MAX_RETRIES)))
                )
                return False

    return False


def init_neo4j_indexes_cloudrun():
    """
    Inicjalizuj Neo4j indexes w Cloud Run environment.

    Tworzy dwa typy indeksów:
    1. Chunk indexes (vector + fulltext dla RAGChunk) - CRITICAL dla RAG
    2. Graph indexes (fulltext dla demographic nodes) - PERFORMANCE dla GraphRAG

    Returns:
        0 - Success (all indexes created)
        1 - Fatal error (Neo4j unreachable, chunk indexes failed)
        2 - Partial success (chunks OK, graph indexes failed - non-critical)
    """
    log_structured("INFO", "=== NEO4J INDEXES INITIALIZATION (Cloud Run) ===")
    log_structured("INFO", "Pipeline: connectivity check → chunk indexes → graph indexes")

    # STEP 1: Test connectivity
    log_structured("INFO", "STEP 1/3: Testing Neo4j connectivity...")
    if not test_neo4j_connectivity():
        log_structured(
            "ERROR",
            "Cannot proceed with index creation - Neo4j is unreachable",
            troubleshooting=[
                "Check Neo4j AuraDB status at console.neo4j.io",
                "Verify NEO4J_URI secret is correct",
                "Verify NEO4J_PASSWORD secret is correct",
                "Check firewall rules (allow Cloud Run IP ranges)",
                "Ensure Neo4j instance is in same region (europe-west1)"
            ]
        )
        return 1  # Fatal error

    # STEP 2: Create chunk indexes (vector + fulltext for RAGChunk nodes)
    # CRITICAL - bez tych indeksów RAG w ogóle nie zadziała
    log_structured("INFO", "STEP 2/3: Creating indexes for RAG chunks (vector + fulltext)...")

    try:
        from scripts.init_neo4j_indexes import init_neo4j_indexes

        chunks_success = init_neo4j_indexes()

        if not chunks_success:
            log_structured(
                "ERROR",
                "❌ Chunk indexes initialization FAILED",
                impact="RAG system will not work - vector/keyword search requires these indexes",
                indexes=["rag_document_embeddings (vector)", "rag_fulltext_index (fulltext)"]
            )
            return 1  # Fatal error - bez chunk indexes RAG nie zadziała

        log_structured(
            "INFO",
            "✅ Chunk indexes created successfully",
            indexes=["rag_document_embeddings (vector)", "rag_fulltext_index (fulltext)"]
        )

    except Exception as e:
        log_structured(
            "ERROR",
            "❌ Unexpected error during chunk index initialization",
            error=str(e),
            exception_type=type(e).__name__
        )
        import traceback
        log_structured("ERROR", "Traceback", traceback=traceback.format_exc())
        return 1  # Fatal error

    # STEP 3: Create graph indexes (fulltext for graph demographic nodes)
    # NON-CRITICAL - system może działać bez tego (queries będą wolniejsze)
    log_structured("INFO", "STEP 3/3: Creating fulltext index for graph nodes...")

    try:
        from scripts.add_graph_fulltext_indexes import add_graph_fulltext_indexes

        graph_success = add_graph_fulltext_indexes()

        if graph_success:
            log_structured(
                "INFO",
                "✅ Graph fulltext index created successfully",
                index="graph_demographic_fulltext",
                performance="GraphRAG queries will be 60x+ faster (<500ms vs 10-30s)"
            )
        else:
            log_structured(
                "WARNING",
                "⚠️  Graph fulltext index initialization failed",
                index="graph_demographic_fulltext",
                impact="Non-critical - GraphRAG will fall back to slower CONTAINS queries",
                note="System will continue to work but persona generation may be slower"
            )
            return 2  # Partial success - chunks OK, graph failed

    except Exception as e:
        log_structured(
            "WARNING",
            "⚠️  Graph fulltext index initialization error",
            error=str(e)[:200],  # Truncate long errors
            exception_type=type(e).__name__,
            impact="Non-critical - GraphRAG will use slower queries",
            note="System can continue without graph fulltext index"
        )
        return 2  # Partial success - chunks OK, graph error

    # All successful
    log_structured(
        "INFO",
        "✅ All Neo4j indexes initialized successfully",
        total_indexes=3,
        chunk_indexes=["rag_document_embeddings", "rag_fulltext_index"],
        graph_indexes=["graph_demographic_fulltext"]
    )
    return 0  # Success


if __name__ == "__main__":
    log_structured(
        "INFO",
        "Cloud Run Job started",
        job="neo4j-init",
        environment=settings.ENVIRONMENT,
        neo4j_uri=settings.NEO4J_URI[:30] + "..." if len(settings.NEO4J_URI) > 30 else settings.NEO4J_URI
    )

    exit_code = init_neo4j_indexes_cloudrun()

    log_structured(
        "INFO" if exit_code == 0 else "WARNING" if exit_code == 2 else "ERROR",
        "Cloud Run Job completed",
        exit_code=exit_code,
        status="success" if exit_code == 0 else "partial_success" if exit_code == 2 else "failed"
    )

    sys.exit(exit_code)
