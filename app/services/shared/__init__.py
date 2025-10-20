"""
Shared services and utilities.

Wspólne komponenty używane przez różne serwisy:
- clients.py - LLM clients builder, shared utilities
"""

from .clients import build_chat_model

__all__ = [
    "build_chat_model",
]
