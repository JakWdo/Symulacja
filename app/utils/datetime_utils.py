"""Utilities for working with timezone-aware datetimes.

This module provides utility functions to ensure consistent use of
timezone-aware datetime objects throughout the application, preventing
"naive vs aware" datetime comparison errors.
"""

from datetime import datetime, timezone
from typing import Optional


def get_utc_now() -> datetime:
    """Pobiera aktualny czas UTC jako timezone-aware datetime.

    Returns:
        datetime: Aktualny czas UTC ze strefą czasową (timezone-aware).

    Example:
        >>> now = get_utc_now()
        >>> now.tzinfo is not None
        True
        >>> str(now.tzinfo)
        'UTC'

    Note:
        Używaj tej funkcji zamiast datetime.utcnow(), która zwraca naive datetime.
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Konwertuje naive datetime na timezone-aware UTC datetime.

    Jeśli datetime jest już timezone-aware, zwraca go bez zmian.
    Jeśli datetime jest naive (bez timezone), zakłada że jest w UTC
    i dodaje timezone information.

    Args:
        dt: Datetime object do konwersji, lub None.

    Returns:
        datetime: Timezone-aware datetime w UTC, lub None jeśli input był None.

    Example:
        >>> naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        >>> aware_dt = ensure_utc(naive_dt)
        >>> aware_dt.tzinfo is not None
        True

    Note:
        Jeśli datetime jest naive, funkcja zakłada że reprezentuje czas UTC.
        Jeśli czas jest w innej strefie, użyj .astimezone(timezone.utc).
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - zakładamy UTC
        return dt.replace(tzinfo=timezone.utc)

    # Already timezone-aware
    return dt
