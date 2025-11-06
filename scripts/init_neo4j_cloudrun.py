#!/usr/bin/env python3
"""
Inicjalizacja Neo4j Indexes dla Cloud Run Deployment

Wrapper dla init_neo4j_indexes.py z dodatkowymi features dla Cloud Run:
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
    0 - Success (indexes created or already exist)
    1 - Fatal error (Neo4j unreachable, auth failed)
    2 - Partial success (some indexes failed but not critical)
"""

import sys
import time
import logging
from pathlib import Path

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from config import app as app_config

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
    log_structured("INFO", "Testing Neo4j connectivity", uri=app_config.neo4j.uri)

    delay = INITIAL_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver = GraphDatabase.driver(
                app_config.neo4j.uri,
                auth=(app_config.neo4j.user, app_config.neo4j.password),
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

    Returns:
        0 - Success
        1 - Fatal error
        2 - Partial success
    """
    log_structured("INFO", "=== NEO4J INDEXES INITIALIZATION (Cloud Run) ===")

    # STEP 1: Test connectivity
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

    # STEP 2: Create indexes (używamy istniejącego skryptu)
    log_structured("INFO", "Starting index creation")

    try:
        from scripts.init_neo4j_indexes import init_neo4j_indexes

        success = init_neo4j_indexes()

        if success:
            log_structured("INFO", "✅ Neo4j indexes initialized successfully")
            return 0  # Success
        else:
            log_structured(
                "WARNING",
                "⚠️  Index initialization completed with warnings",
                note="Some indexes may have failed but system can continue"
            )
            return 2  # Partial success

    except Exception as e:
        log_structured(
            "ERROR",
            "❌ Unexpected error during index initialization",
            error=str(e),
            exception_type=type(e).__name__
        )
        import traceback
        log_structured("ERROR", "Traceback", traceback=traceback.format_exc())
        return 1  # Fatal error


if __name__ == "__main__":
    log_structured(
        "INFO",
        "Cloud Run Job started",
        job="neo4j-init",
        environment=app_config.environment,
        neo4j_uri=app_config.neo4j.uri[:30] + "..." if len(app_config.neo4j.uri) > 30 else app_config.neo4j.uri
    )

    exit_code = init_neo4j_indexes_cloudrun()

    log_structured(
        "INFO" if exit_code == 0 else "WARNING" if exit_code == 2 else "ERROR",
        "Cloud Run Job completed",
        exit_code=exit_code,
        status="success" if exit_code == 0 else "partial_success" if exit_code == 2 else "failed"
    )

    sys.exit(exit_code)
