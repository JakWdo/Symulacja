"""Global pytest configuration hooks."""

from __future__ import annotations

import asyncio
from typing import Iterable

import pytest

_CUSTOM_MARKERS: dict[str, str] = {
    "integration": "marks tests as integration tests (requires database)",
    "e2e": "marks tests as end-to-end checks of the public API",
    "slow": "marks slow-running tests",
    "external": "marks tests that depend on external services or network access",
    "manual": "marks tests meant for manual execution only",
    "performance": "marks performance benchmarks that are expensive to run",
}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register command line flags used to include optional test classes."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Execute tests marked as slow.",
    )
    parser.addoption(
        "--run-external",
        action="store_true",
        default=False,
        help="Execute tests that call external services.",
    )
    parser.addoption(
        "--run-manual",
        action="store_true",
        default=False,
        help="Execute diagnostic/manual tests.",
    )
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Execute performance benchmark tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Expose custom markers to pytest --markers output and plugins."""
    for name, description in _CUSTOM_MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {description}")


def _should_skip(item: pytest.Item, marker: str, enabled: bool) -> bool:
    return marker in item.keywords and not enabled and not item.get_closest_marker("override_skip")


def pytest_collection_modifyitems(config: pytest.Config, items: Iterable[pytest.Item]) -> None:
    """
    Automatically annotate collected tests and skip heavy classes unless requested.

    - Async coroutine tests receive the pytest-asyncio marker automatically.
    - Tests that require the `db_session` fixture are marked as integration tests.
    - Slow/external/manual/performance suites are skipped by default to keep CI fast.
    """
    for item in items:
        if asyncio.iscoroutinefunction(getattr(item.function, "__wrapped__", item.function)):
            item.add_marker(pytest.mark.asyncio)

        if "db_session" in item.fixturenames:
            item.add_marker(pytest.mark.integration)

        if _should_skip(item, "slow", config.getoption("--run-slow")):
            item.add_marker(pytest.mark.skip(reason="Skipping slow test. Use --run-slow to enable."))
        if _should_skip(
            item,
            "external",
            config.getoption("--run-external"),
        ):
            item.add_marker(pytest.mark.skip(reason="Skipping external-service test. Use --run-external to enable."))
        if _should_skip(item, "manual", config.getoption("--run-manual")):
            item.add_marker(pytest.mark.skip(reason="Skipping manual test. Use --run-manual to enable."))
        if _should_skip(
            item,
            "performance",
            config.getoption("--run-performance"),
        ):
            item.add_marker(pytest.mark.skip(reason="Skipping performance benchmark. Use --run-performance to enable."))
