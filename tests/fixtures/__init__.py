"""
Modular Pytest fixtures used across the test suite.

Keeping fixtures in dedicated modules improves discoverability and makes it
easier to reason about dependencies between slow integration resources and
lightweight unit helpers.
"""

pytest_plugins = [
    "tests.fixtures.asyncio_loop",
    "tests.fixtures.config",
    "tests.fixtures.database",
    "tests.fixtures.api",
    "tests.fixtures.samples",
    "tests.fixtures.mocks",
    "tests.fixtures.rag",
    "tests.fixtures.utils",
]

