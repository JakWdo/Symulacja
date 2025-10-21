"""AsyncIO event loop fixtures."""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """
    Provide a dedicated event loop for the entire pytest session.

    This avoids warnings about closed loops when pytest-asyncio tears down
    per-test loops and keeps async fixtures predictable.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

