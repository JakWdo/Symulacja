"""
Stopwords Loader - Centralized stopwords loading from YAML.

Ładuje stopwords z config/prompts/shared/stopwords.yaml zamiast
duplikować je w wielu miejscach w kodzie.

Usage:
    from config.stopwords_loader import get_polish_stopwords, get_english_stopwords

    polish = get_polish_stopwords()
    english = get_english_stopwords()
"""

import logging
from pathlib import Path
from typing import Set

import yaml

logger = logging.getLogger(__name__)

# Config root directory
CONFIG_ROOT = Path(__file__).parent.resolve()
STOPWORDS_FILE = CONFIG_ROOT / "prompts" / "shared" / "stopwords.yaml"


def load_stopwords_from_yaml() -> dict:
    """
    Load stopwords from YAML file.

    Returns:
        Dict z kluczami 'polish' i 'english', każdy zawiera listę stopwords
    """
    if not STOPWORDS_FILE.exists():
        logger.warning(f"Stopwords file not found: {STOPWORDS_FILE}")
        return {"polish": [], "english": []}

    try:
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse stopwords YAML: {e}")
        return {"polish": [], "english": []}


# Cache stopwords (loaded once per process)
_STOPWORDS_CACHE = None


def _get_stopwords_cache() -> dict:
    """Get cached stopwords or load them."""
    global _STOPWORDS_CACHE
    if _STOPWORDS_CACHE is None:
        _STOPWORDS_CACHE = load_stopwords_from_yaml()
    return _STOPWORDS_CACHE


def get_polish_stopwords() -> Set[str]:
    """
    Get Polish stopwords as a set.

    Returns:
        Set of Polish stopwords
    """
    data = _get_stopwords_cache()
    return set(data.get("polish", []))


def get_english_stopwords() -> Set[str]:
    """
    Get English stopwords as a set.

    Returns:
        Set of English stopwords
    """
    data = _get_stopwords_cache()
    return set(data.get("english", []))


def get_all_stopwords() -> Set[str]:
    """
    Get all stopwords (Polish + English) as a set.

    Returns:
        Set of all stopwords
    """
    return get_polish_stopwords() | get_english_stopwords()
