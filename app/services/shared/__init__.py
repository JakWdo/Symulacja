"""
Shared services and utilities.

Wspólne komponenty używane przez różne serwisy:
- clients.py - LLM clients builder, shared utilities
- rag_provider.py - RAG singleton provider (PolishSocietyRAG)
"""

from .clients import build_chat_model, get_embeddings
from .rag_provider import get_polish_society_rag, reset_polish_society_rag

__all__ = [
    "build_chat_model",
    "get_embeddings",
    "get_polish_society_rag",
    "reset_polish_society_rag",
]
