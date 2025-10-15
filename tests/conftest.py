"""
Lightweight pytest bootstrapper.

All fixtures now live in the ``tests/fixtures`` package to keep responsibilities
separated and speed up discovery of domain-specific helpers.
"""

pytest_plugins = ["tests.fixtures"]

