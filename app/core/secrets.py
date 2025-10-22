"""
Google Cloud Secret Manager integration for Sight.

Provides secure access to secrets stored in Google Cloud Secret Manager
with automatic fallback to environment variables for local development.

Usage:
    from app.core.secrets import get_secret

    api_key = get_secret("GOOGLE_API_KEY")

Notes:
    - In production (ENVIRONMENT=production): Fetches from Secret Manager
    - In development: Falls back to local environment variables
    - Results are cached using @lru_cache for performance
"""

import os
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def get_secret(secret_id: str, project_id: Optional[str] = None) -> str:
    """
    Retrieve secret from Google Cloud Secret Manager with fallback to env vars.

    Args:
        secret_id: ID of the secret (e.g., "GOOGLE_API_KEY")
        project_id: GCP project ID (auto-detected if None)

    Returns:
        Secret value as string

    Raises:
        RuntimeError: If secret cannot be retrieved in production
        ValueError: If secret not found in development

    Examples:
        >>> get_secret("GOOGLE_API_KEY")  # Production: from Secret Manager
        'AIza...'

        >>> get_secret("DATABASE_URL")  # Development: from env var
        'postgresql+asyncpg://...'
    """
    environment = os.getenv("ENVIRONMENT", "development")

    # Development mode: Use environment variables
    if environment != "production":
        value = os.getenv(secret_id)
        if value:
            logger.debug(f"Using local env var for secret '{secret_id}'")
            return value
        else:
            raise ValueError(
                f"Secret '{secret_id}' not found in environment variables. "
                f"Set {secret_id} in .env file or environment."
            )

    # Production mode: Use Google Cloud Secret Manager
    try:
        from google.cloud import secretmanager

        if not project_id:
            # Auto-detect project ID from metadata server
            try:
                import google.auth
                _, project_id = google.auth.default()
            except Exception as e:
                logger.error(f"Failed to auto-detect GCP project ID: {e}")
                raise RuntimeError(
                    f"Cannot auto-detect GCP project ID. "
                    f"Please provide project_id parameter or set GOOGLE_CLOUD_PROJECT env var."
                )

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

        # Retry logic for transient failures
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = client.access_secret_version(request={"name": name})
                payload = response.payload.data.decode("UTF-8")
                logger.info(f"✅ Secret '{secret_id}' loaded from Secret Manager")
                return payload
            except Exception as exc:
                if attempt >= max_retries:
                    logger.error(
                        f"❌ Failed to load secret '{secret_id}' after {max_retries} attempts: {exc}"
                    )
                    raise RuntimeError(f"Cannot load secret '{secret_id}': {exc}")
                logger.warning(f"⚠️ Retry {attempt}/{max_retries} for secret '{secret_id}'")

    except ImportError:
        logger.error(
            "google-cloud-secret-manager not installed. "
            "Install with: pip install google-cloud-secret-manager"
        )
        raise RuntimeError(
            "google-cloud-secret-manager not installed. Required for production deployment."
        )
