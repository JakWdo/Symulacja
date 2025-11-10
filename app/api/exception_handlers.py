"""
Global Exception Handlers

Centralized exception handling for FastAPI application.
Handles validation errors, HTTP exceptions, and unexpected errors with detailed logging.
"""

import json
import logging
import os
import traceback
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)

# Debug mode from environment
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Obsłuż błędy walidacji REQUEST (422 Unprocessable Entity)

    Loguje pełne szczegóły błędów walidacji dla debugowania w GCP Logs.
    """
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error.get("type"),
            "input": error.get("input"),
        })

    # Format logowania przyjazny dla GCP (textPayload, nie structured extra fields)
    error_msg = (
        f"Request validation error: {request.method} {request.url.path}\n"
        f"Error count: {len(errors)}\n"
        f"Validation errors:\n{json.dumps(error_details, indent=2, ensure_ascii=False)}\n"
        f"Request body: {exc.body if hasattr(exc, 'body') else 'N/A'}"
    )

    logger.error(error_msg, exc_info=False)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )


async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    """
    Obsłuż błędy walidacji RESPONSE (500 Internal Server Error)

    To jest KRYTYCZNY błąd - znaczy że endpoint zwrócił response niezgodny ze schematem.
    Loguje pełne szczegóły dla debugowania.
    """
    errors = exc.errors()
    error_details = []
    for error in errors:
        error_details.append({
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error.get("type"),
        })

    # Format logowania przyjazny dla GCP (textPayload)
    error_msg = (
        f"RESPONSE VALIDATION ERROR: {request.method} {request.url.path} - Schema mismatch!\n"
        f"Error count: {len(errors)}\n"
        f"Validation errors:\n{json.dumps(error_details, indent=2, ensure_ascii=False)}\n"
        f"Response body (first 500 chars): {str(exc.body)[:500] if hasattr(exc, 'body') else 'N/A'}"
    )

    logger.critical(error_msg, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Response validation error. This is a server bug, please report it."},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Obsłuż HTTPException (4xx, 5xx) z detailed logging

    Loguje szczegóły HTTP errors (404, 401, 403, etc.) dla debugowania.
    """
    # Format logowania przyjazny dla GCP (textPayload)
    error_msg = (
        f"HTTP {exc.status_code}: {request.method} {request.url.path}\n"
        f"Detail: {exc.detail}\n"
        f"Headers: {dict(exc.headers) if exc.headers else 'None'}"
    )

    logger.warning(error_msg, exc_info=False)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


async def global_exception_handler(request: Request, exc: Exception):
    """
    Obsłuż wszystkie nieobsłużone wyjątki

    Zapobiega wyciekom szczegółów błędów w produkcji.
    W development zwraca pełny stack trace, w production tylko ogólny komunikat.

    Args:
        request: FastAPI Request
        exc: Wyjątek który nie został obsłużony

    Returns:
        JSONResponse z kodem 500 i bezpiecznym komunikatem błędu
    """
    tb = traceback.format_exc()

    # Format logowania przyjazny dla GCP (textPayload)
    error_msg = (
        f"Unhandled exception: {request.method} {request.url.path}\n"
        f"Exception type: {type(exc).__name__}\n"
        f"Exception message: {str(exc)}\n"
        f"Traceback:\n{tb}"
    )

    logger.error(error_msg, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            # W DEBUG pokazuj szczegóły, w produkcji ukryj
            "error": str(exc) if DEBUG else "An unexpected error occurred",
        },
    )


def register_exception_handlers(app: FastAPI):
    """
    Register all exception handlers with the FastAPI app.

    This function should be called during app initialization in main.py.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("✓ Exception handlers registered")
