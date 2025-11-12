"""
Infrastructure Health Check Service

Sprawdza zdrowie kluczowych serwisów infrastruktury:
- PostgreSQL (database)
- Redis (cache)
- Neo4j (graph database)
"""

import asyncio
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import logger


class InfrastructureHealthService:
    """
    Serwis do sprawdzania zdrowia infrastruktury

    Używany przez /health endpoint dla Cloud Run health checks
    i automatic rollback policy.
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        redis_client: Redis | None = None,
    ):
        """
        Inicjalizuj serwis

        Args:
            db: Async SQLAlchemy session (optional)
            redis_client: Redis async client (optional)
        """
        self.db = db
        self.redis_client = redis_client

    async def check_database(self, timeout: float = 2.0) -> dict[str, Any]:
        """
        Sprawdź połączenie z PostgreSQL

        Args:
            timeout: Timeout w sekundach (default 2s)

        Returns:
            {
                "status": "healthy" | "unhealthy",
                "latency_ms": float,
                "error": str | None
            }
        """
        if not self.db:
            return {
                "status": "unhealthy",
                "error": "Database session not initialized",
                "latency_ms": 0,
            }

        try:
            import time

            start = time.time()

            # Simple query to test connection
            result = await asyncio.wait_for(
                self.db.execute(text("SELECT 1")), timeout=timeout
            )
            latency_ms = (time.time() - start) * 1000

            return {"status": "healthy", "latency_ms": round(latency_ms, 2), "error": None}

        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": f"Database timeout (>{timeout}s)",
                "latency_ms": timeout * 1000,
            }
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}")
            return {
                "status": "unhealthy",
                "error": f"Database error: {str(exc)[:100]}",
                "latency_ms": 0,
            }

    async def check_redis(self, timeout: float = 2.0) -> dict[str, Any]:
        """
        Sprawdź połączenie z Redis

        Args:
            timeout: Timeout w sekundach (default 2s)

        Returns:
            {
                "status": "healthy" | "unhealthy",
                "latency_ms": float,
                "error": str | None
            }
        """
        if not self.redis_client:
            return {
                "status": "unhealthy",
                "error": "Redis client not initialized",
                "latency_ms": 0,
            }

        try:
            import time

            start = time.time()

            # Ping Redis
            response = await asyncio.wait_for(
                self.redis_client.ping(), timeout=timeout
            )
            latency_ms = (time.time() - start) * 1000

            if response:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "error": None,
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis ping failed",
                    "latency_ms": round(latency_ms, 2),
                }

        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": f"Redis timeout (>{timeout}s)",
                "latency_ms": timeout * 1000,
            }
        except Exception as exc:
            logger.error(f"Redis health check failed: {exc}")
            return {
                "status": "unhealthy",
                "error": f"Redis error: {str(exc)[:100]}",
                "latency_ms": 0,
            }

    async def check_neo4j(self, timeout: float = 2.0) -> dict[str, Any]:
        """
        Sprawdź połączenie z Neo4j

        Args:
            timeout: Timeout w sekundach (default 2s)

        Returns:
            {
                "status": "healthy" | "unhealthy",
                "latency_ms": float,
                "error": str | None
            }
        """
        try:
            from app.services.shared.neo4j_client import get_neo4j_driver
            import time

            driver = get_neo4j_driver()
            if not driver:
                return {
                    "status": "unhealthy",
                    "error": "Neo4j driver not initialized",
                    "latency_ms": 0,
                }

            start = time.time()

            # Verify connectivity with simple query
            async with driver.session() as session:
                result = await asyncio.wait_for(
                    session.run("RETURN 1 AS test"), timeout=timeout
                )
                await result.consume()

            latency_ms = (time.time() - start) * 1000

            return {"status": "healthy", "latency_ms": round(latency_ms, 2), "error": None}

        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": f"Neo4j timeout (>{timeout}s)",
                "latency_ms": timeout * 1000,
            }
        except Exception as exc:
            logger.error(f"Neo4j health check failed: {exc}")
            return {
                "status": "unhealthy",
                "error": f"Neo4j error: {str(exc)[:100]}",
                "latency_ms": 0,
            }

    async def check_all(self, timeout: float = 2.0) -> dict[str, Any]:
        """
        Sprawdź wszystkie serwisy równolegle

        Args:
            timeout: Timeout per service w sekundach (default 2s)

        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "checks": {
                    "database": {...},
                    "redis": {...},
                    "neo4j": {...}
                },
                "latency_total_ms": float
            }
        """
        import time

        start = time.time()

        # Run all checks in parallel
        db_check, redis_check, neo4j_check = await asyncio.gather(
            self.check_database(timeout),
            self.check_redis(timeout),
            self.check_neo4j(timeout),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        if isinstance(db_check, Exception):
            db_check = {
                "status": "unhealthy",
                "error": f"Check failed: {str(db_check)}",
                "latency_ms": 0,
            }
        if isinstance(redis_check, Exception):
            redis_check = {
                "status": "unhealthy",
                "error": f"Check failed: {str(redis_check)}",
                "latency_ms": 0,
            }
        if isinstance(neo4j_check, Exception):
            neo4j_check = {
                "status": "unhealthy",
                "error": f"Check failed: {str(neo4j_check)}",
                "latency_ms": 0,
            }

        latency_total_ms = (time.time() - start) * 1000

        checks = {"database": db_check, "redis": redis_check, "neo4j": neo4j_check}

        # Determine overall status
        unhealthy_count = sum(1 for check in checks.values() if check["status"] == "unhealthy")

        if unhealthy_count == 0:
            overall_status = "healthy"
        elif unhealthy_count <= 1:
            overall_status = "degraded"  # 1 service down = degraded
        else:
            overall_status = "unhealthy"  # 2+ services down = unhealthy

        return {
            "status": overall_status,
            "checks": checks,
            "latency_total_ms": round(latency_total_ms, 2),
        }
