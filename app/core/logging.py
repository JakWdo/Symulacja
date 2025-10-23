"""Konfiguracja loggingu dla aplikacji Sight.

Ten moduł konfiguruje logging dla różnych środowisk:
- Development: Plain text logs do console (DEBUG level)
- Production: Structured JSON logs dla Cloud Logging (INFO level)

Użycie:
    from app.core.logging import setup_logging
    setup_logging()  # Wywołaj przed utworzeniem FastAPI app
"""

import json
import logging
import logging.config
import sys
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.core.config import get_settings

settings = get_settings()


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that safely handles common Python types not supported by default.

    Supports:
    - bool, int, float, str, None (default types)
    - datetime, date → ISO format string
    - UUID → string
    - bytes → UTF-8 decoded string

    For any other type, falls back to str() representation.
    """

    def default(self, obj):
        """Convert non-serializable objects to JSON-safe formats."""
        # Basic types (explicitly handled for clarity)
        if isinstance(obj, (bool, int, float, str, type(None))):
            return obj

        # Date and time objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        # UUID objects
        if isinstance(obj, UUID):
            return str(obj)

        # Bytes objects
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')

        # Fallback: convert to string
        return str(obj)


class JSONFormatter(logging.Formatter):
    """Custom formatter dla strukturalnych logów JSON (Cloud Logging)."""

    def format(self, record: logging.LogRecord) -> str:
        """Formatuje log record jako JSON dla Cloud Logging.

        Args:
            record: Log record do formatowania

        Returns:
            JSON string z severity, message, timestamp, extra fields
        """
        import json
        from datetime import datetime, timezone

        # Base log entry
        log_entry: dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields (from logger.info(..., extra={...}))
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
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
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "getMessage",
                ]:
                    log_entry[key] = value

        # Add exception info if present
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)

        # Use SafeJSONEncoder to handle bool, datetime, UUID, etc.
        return json.dumps(log_entry, ensure_ascii=False, cls=SafeJSONEncoder)


def setup_logging() -> None:
    """Setup logging configuration based on environment settings.

    Konfiguruje:
    - Log level z settings.LOG_LEVEL
    - Structured JSON logs (production) vs plain text (development)
    - Handlers dla stdout/stderr
    - Disable propagation dla noisy libraries (httpx, httpcore)
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Base logging config
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "plain": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json" if settings.STRUCTURED_LOGGING else "plain",
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # Uvicorn/Gunicorn loggers
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "gunicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "gunicorn.error": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "gunicorn.access": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # FastAPI
            "fastapi": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy (reduce noise in production)
            "sqlalchemy.engine": {
                "level": logging.WARNING if settings.ENVIRONMENT == "production" else logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
            # Reduce noise from HTTP clients (httpx, httpcore używane przez LangChain)
            "httpx": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
            "httpcore": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
            # LangChain logging (może być noisy)
            "langchain": {
                "level": logging.INFO if settings.DEBUG else logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Apply configuration
    logging.config.dictConfig(config)

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": settings.LOG_LEVEL,
            "structured_logging": settings.STRUCTURED_LOGGING,
            "environment": settings.ENVIRONMENT,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello", extra={"user_id": 123})
    """
    return logging.getLogger(name)
