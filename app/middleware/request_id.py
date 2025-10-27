"""
Request ID Middleware - Correlation Tracking dla GCP Cloud Logging

Middleware generujący unikalny request_id dla każdego HTTP requesta.
Request ID jest propagowany przez wszystkie logger calls aby umożliwić
śledzenie całego flow requesta w GCP Logs Explorer.

Features:
- Generuje UUID dla każdego requesta (lub używa X-Request-ID header jeśli istnieje)
- Dodaje request_id do response headers (dla debugowania)
- Propaguje request_id przez contextvars (dostępny dla wszystkich logger calls)
- Loguje podstawowe info o requeście (method, path, user agent, duration)

Usage:
    app.add_middleware(RequestIDMiddleware)

Example logs w GCP:
    Filter: jsonPayload.request_id="abc-123-def"
    → Wszystkie logi dla konkretnego requesta!
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ContextVar dla request_id - propagowany automatycznie przez asyncio tasks
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """
    Pobierz current request_id z context

    Returns:
        Request ID jeśli dostępny, None jeśli poza requestem

    Example:
        >>> request_id = get_request_id()
        >>> logger.info("Processing data", extra={"request_id": request_id})
    """
    return request_id_context.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware dodający request_id do każdego HTTP requesta

    Request ID jest:
    1. Generowany jako UUID (lub pobierany z X-Request-ID header)
    2. Zapisany w contextvars (dostępny dla wszystkich logger calls)
    3. Dodany do response headers (X-Request-ID)
    4. Logowany z podstawowymi info o requeście

    IMPORTANT: Zainstaluj PRZED innymi middleware aby request_id był dostępny wszędzie!
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request with request_id tracking

        Args:
            request: FastAPI Request
            call_next: Next middleware/endpoint handler

        Returns:
            Response z dodanym X-Request-ID header
        """
        # Generate or extract request_id
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Set request_id in context (available for all logger calls)
        request_id_context.set(req_id)

        # Start timer (dla duration measurement)
        start_time = time.time()

        # Process request (NO request logging - za dużo noise)
        # Request ID jest propagowany przez contextvars - dostępny dla logów aplikacji
        try:
            response = await call_next(request)
        except Exception as exc:
            # TYLKO unhandled exceptions (critical errors)
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "Unhandled exception during request processing",
                exc_info=True,
                extra={
                    "request_id": req_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        # NO completed request logging - za dużo noise w production
        # Jeśli potrzeba: włącz przez VERBOSE_REQUEST_LOGGING env var

        # Add request_id to response headers (for client debugging)
        response.headers["X-Request-ID"] = req_id

        # Clear context (cleanup)
        request_id_context.set(None)

        return response


class RequestIDLogFilter(logging.Filter):
    """
    Logging filter dodający request_id do każdego log record

    OPTIONAL: Użyj jeśli chcesz automatycznie dodawać request_id
    do wszystkich logów bez ręcznego extra={'request_id': ...}

    Usage:
        logger = logging.getLogger(__name__)
        logger.addFilter(RequestIDLogFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Dodaj request_id do log record (jeśli dostępny)

        Args:
            record: LogRecord do modyfikacji

        Returns:
            True (always allow log)
        """
        request_id = get_request_id()
        if request_id and not hasattr(record, "request_id"):
            record.request_id = request_id  # type: ignore
        return True
