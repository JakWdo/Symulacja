"""
Core shared services.

Utility services used across different modules.
"""

from .clients import build_chat_model, get_embeddings

__all__ = [
    "build_chat_model",
    "get_embeddings",
]
