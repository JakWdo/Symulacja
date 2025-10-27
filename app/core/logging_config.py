"""
Logging Configuration - Structured Logging dla GCP Cloud Logging

Module ten konfiguruje strukturalne logowanie w formacie JSON dla łatwego
filtrowania i analizy w GCP Logs Explorer.

Features:
- JSON formatter dla GCP Cloud Logging (STRUCTURED_LOGGING=True)
- Standard formatter dla development (human-readable)
- Request correlation tracking (request_id w każdym logu)
- Automatic severity mapping (INFO → INFO, ERROR → ERROR, etc.)

Używane przez app/main.py podczas startu aplikacji.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    JSON Formatter dla GCP Cloud Logging

    Format kompatybilny z GCP Logs Explorer:
    {
        "severity": "INFO",
        "message": "User logged in",
        "timestamp": "2025-10-27T10:30:45.123456Z",
        "request_id": "abc123",
        "user_id": "user-456",
        ...extra fields...
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formatuj log record jako JSON

        Args:
            record: LogRecord z logging module

        Returns:
            JSON string kompatybilny z GCP Cloud Logging
        """
        # Podstawowe pola (wymagane przez GCP)
        log_data: dict[str, Any] = {
            "severity": record.levelname,  # INFO, WARNING, ERROR, CRITICAL
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Dodaj exception info jeśli dostępne
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        # Dodaj stack trace jeśli dostępny
        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        # Dodaj extra fields (np. request_id, user_id, project_id)
        # Extra fields są przekazywane przez logger.info(..., extra={'request_id': '123'})
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                # Skip built-in attributes
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "taskName",
                ]:
                    # Serialize complex objects
                    try:
                        if isinstance(value, (str, int, float, bool, type(None))):
                            log_data[key] = value
                        else:
                            log_data[key] = str(value)
                    except Exception:
                        # Skip non-serializable fields
                        pass

        return json.dumps(log_data, ensure_ascii=False)


def configure_logging(
    structured: bool = False,
    level: str = "INFO",
) -> None:
    """
    Konfiguruj logging dla aplikacji

    Args:
        structured: Czy używać JSON formatter (True dla production)
        level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> # Development (human-readable)
        >>> configure_logging(structured=False, level="DEBUG")
        >>>
        >>> # Production (JSON dla GCP)
        >>> configure_logging(structured=True, level="INFO")
    """
    # Wybierz formatter
    if structured:
        formatter = JSONFormatter()
    else:
        # Human-readable format dla development
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers (avoid duplicates)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Silence noisy third-party loggers (production best practice)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # HTTP access logs (za dużo noise)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # HTTP client logs
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # HTTP core logs
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)  # HTTP/1.1 protocol logs
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)  # Connection pool logs

    # Silence Neo4j driver debug logs (BARDZO verbose - routing, pooling, Cypher queries)
    logging.getLogger("neo4j").setLevel(logging.WARNING)  # Neo4j driver root logger
    logging.getLogger("neo4j.io").setLevel(logging.WARNING)  # Neo4j I/O operations
    logging.getLogger("neo4j.pool").setLevel(logging.WARNING)  # Connection pooling
    logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)  # Bolt protocol

    # Log configuration success
    mode = "structured (JSON)" if structured else "standard (human-readable)"
    root_logger.info(f"✓ Logging configured: mode={mode}, level={level}")
