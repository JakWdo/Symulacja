#!/usr/bin/env python3
"""
Data Manager - Centralne zarządzanie danymi pluginu Learn-by-Doing

Odpowiedzialności:
- Ładowanie i zapisywanie danych (progress, config, knowledge base, practice log)
- Walidacja struktur danych
- Migracja starych formatów
- Error handling i graceful fallbacks
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ścieżki
PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"
PROMPTS_DIR = PLUGIN_ROOT / "prompts"

# Upewnij się że katalogi istnieją
DATA_DIR.mkdir(exist_ok=True, parents=True)
PROMPTS_DIR.mkdir(exist_ok=True, parents=True)


# ============================================================================
# LOADING FUNCTIONS
# ============================================================================

def load_progress() -> Dict[str, Any]:
    """
    Wczytaj postęp uczenia się z learning_progress.json

    Returns:
        Dict z postępem. W przypadku błędu zwraca domyślną strukturę.
    """
    progress_file = DATA_DIR / "learning_progress.json"

    try:
        if not progress_file.exists():
            logger.info("learning_progress.json nie istnieje, tworzę domyślną strukturę")
            default_progress = _get_default_progress()
            save_progress(default_progress)
            return default_progress

        content = progress_file.read_text(encoding='utf-8')
        if not content.strip():
            logger.warning("learning_progress.json jest pusty, używam domyślnej struktury")
            default_progress = _get_default_progress()
            save_progress(default_progress)
            return default_progress

        progress = json.loads(content)

        # Walidacja i migracja
        progress = validate_and_migrate_progress(progress)

        return progress

    except json.JSONDecodeError as e:
        logger.error(f"Błąd parsowania learning_progress.json: {e}")
        logger.info("Używam domyślnej struktury")
        return _get_default_progress()

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd w load_progress: {e}")
        return _get_default_progress()


def load_config() -> Dict[str, Any]:
    """
    Wczytaj konfigurację z config.json

    Returns:
        Dict z konfiguracją. W przypadku błędu zwraca domyślną konfigurację.
    """
    config_file = DATA_DIR / "config.json"

    try:
        if not config_file.exists():
            logger.info("config.json nie istnieje, używam domyślnej konfiguracji")
            return _get_default_config()

        content = config_file.read_text(encoding='utf-8')
        if not content.strip():
            logger.warning("config.json jest pusty")
            return _get_default_config()

        config = json.loads(content)

        # Merge z domyślną konfiguracją (missing keys)
        default_config = _get_default_config()
        merged_config = {**default_config, **config}

        return merged_config

    except json.JSONDecodeError as e:
        logger.error(f"Błąd parsowania config.json: {e}")
        return _get_default_config()

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd w load_config: {e}")
        return _get_default_config()


def load_knowledge_base() -> Dict[str, Any]:
    """
    Wczytaj bazę wiedzy z knowledge_base.json

    Returns:
        Dict z konceptami i kategoriami. W przypadku błędu zwraca pustą strukturę.
    """
    kb_file = DATA_DIR / "knowledge_base.json"

    try:
        if not kb_file.exists():
            logger.warning("knowledge_base.json nie istnieje")
            return {"concepts": {}, "categories": {}}

        content = kb_file.read_text(encoding='utf-8')
        if not content.strip():
            logger.warning("knowledge_base.json jest pusty")
            return {"concepts": {}, "categories": {}}

        kb = json.loads(content)

        # Walidacja podstawowej struktury
        if "concepts" not in kb:
            kb["concepts"] = {}
        if "categories" not in kb:
            kb["categories"] = {}

        return kb

    except json.JSONDecodeError as e:
        logger.error(f"Błąd parsowania knowledge_base.json: {e}")
        return {"concepts": {}, "categories": {}}

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd w load_knowledge_base: {e}")
        return {"concepts": {}, "categories": {}}


def load_practice_log() -> List[Dict[str, Any]]:
    """
    Wczytaj logi praktyki z practice_log.jsonl

    Returns:
        Lista dict-ów z akcjami. W przypadku błędu zwraca pustą listę.
    """
    log_file = DATA_DIR / "practice_log.jsonl"

    try:
        if not log_file.exists():
            logger.info("practice_log.jsonl nie istnieje")
            return []

        content = log_file.read_text(encoding='utf-8').strip()
        if not content:
            return []

        logs = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue

            try:
                log_entry = json.loads(line)
                logs.append(log_entry)
            except json.JSONDecodeError as e:
                logger.warning(f"Błąd parsowania linii {i} w practice_log.jsonl: {e}")
                # Pomijamy zepsutą linię
                continue

        return logs

    except Exception as e:
        logger.error(f"Nieoczekiwany błąd w load_practice_log: {e}")
        return []


def load_learning_prompt() -> str:
    """
    Wczytaj główny prompt uczący z prompts/learning_mindset.md

    Returns:
        String z promptem. W przypadku błędu zwraca pusty string.
    """
    prompt_file = PROMPTS_DIR / "learning_mindset.md"

    try:
        if not prompt_file.exists():
            logger.warning("learning_mindset.md nie istnieje")
            return ""

        return prompt_file.read_text(encoding='utf-8')

    except Exception as e:
        logger.error(f"Błąd wczytywania learning_mindset.md: {e}")
        return ""


# ============================================================================
# SAVING FUNCTIONS
# ============================================================================

def save_progress(progress: Dict[str, Any]) -> bool:
    """
    Zapisz postęp uczenia się do learning_progress.json

    Args:
        progress: Dict z postępem

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    progress_file = DATA_DIR / "learning_progress.json"

    try:
        content = json.dumps(progress, indent=2, ensure_ascii=False)
        progress_file.write_text(content, encoding='utf-8')
        return True

    except Exception as e:
        logger.error(f"Błąd zapisywania learning_progress.json: {e}")
        return False


def save_config(config: Dict[str, Any]) -> bool:
    """
    Zapisz konfigurację do config.json

    Args:
        config: Dict z konfiguracją

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    config_file = DATA_DIR / "config.json"

    try:
        content = json.dumps(config, indent=2, ensure_ascii=False)
        config_file.write_text(content, encoding='utf-8')
        return True

    except Exception as e:
        logger.error(f"Błąd zapisywania config.json: {e}")
        return False


def append_practice_log(log_entry: Dict[str, Any]) -> bool:
    """
    Dodaj wpis do practice_log.jsonl

    Args:
        log_entry: Dict z akcją

    Returns:
        True jeśli sukces, False jeśli błąd
    """
    log_file = DATA_DIR / "practice_log.jsonl"

    try:
        # Dodaj timestamp jeśli nie ma
        if "timestamp" not in log_entry:
            log_entry["timestamp"] = datetime.now().isoformat()

        line = json.dumps(log_entry, ensure_ascii=False) + "\n"

        with log_file.open("a", encoding='utf-8') as f:
            f.write(line)

        return True

    except Exception as e:
        logger.error(f"Błąd dodawania do practice_log.jsonl: {e}")
        return False


# ============================================================================
# VALIDATION & MIGRATION
# ============================================================================

def validate_and_migrate_progress(progress: Dict[str, Any]) -> Dict[str, Any]:
    """
    Waliduj i zmigruj strukturę learning_progress

    Args:
        progress: Dict z postępem (może być stary format)

    Returns:
        Dict z postępem w nowym formacie
    """
    # Domyślna struktura dla brakujących kluczy
    default = _get_default_progress()

    # Ensure wszystkie podstawowe klucze istnieją
    for key in ["sessions", "streak_days", "last_session", "concepts", "categories_progress", "current_focus", "recommendations"]:
        if key not in progress:
            progress[key] = default.get(key, {})

    # Migracja: stare learning_paths → nowe categories_progress
    if "learning_paths" in progress and "categories_progress" not in progress:
        logger.info("Migrating old learning_paths to categories_progress")
        # Ta migracja będzie rozbudowana gdy stworzymy knowledge_base
        progress["categories_progress"] = {}

    # Usuń przestarzałe klucze
    if "learning_paths" in progress:
        del progress["learning_paths"]
    if "total_concepts" in progress:
        del progress["total_concepts"]
    if "mastered_concepts" in progress:
        del progress["mastered_concepts"]

    # Walidacja concepts
    if not isinstance(progress.get("concepts"), dict):
        progress["concepts"] = {}

    # Walidacja każdego konceptu
    for concept_id, concept_data in list(progress["concepts"].items()):
        if not isinstance(concept_data, dict):
            logger.warning(f"Removing invalid concept: {concept_id}")
            del progress["concepts"][concept_id]
            continue

        # Ensure required fields
        if "name" not in concept_data:
            concept_data["name"] = concept_id
        if "mastery_level" not in concept_data:
            concept_data["mastery_level"] = 1
        if "practice_count" not in concept_data:
            concept_data["practice_count"] = 0

    return progress


# ============================================================================
# DEFAULT STRUCTURES
# ============================================================================

def _get_default_progress() -> Dict[str, Any]:
    """Zwraca domyślną strukturę learning_progress"""
    return {
        "sessions": 0,
        "streak_days": 0,
        "last_session": None,
        "concepts": {},
        "categories_progress": {},
        "current_focus": {
            "category": None,
            "active_concepts": []
        },
        "recommendations": {
            "generated_at": None,
            "next_steps": []
        }
    }


def _get_default_config() -> Dict[str, Any]:
    """Zwraca domyślną konfigurację"""
    return {
        "auto_tracking": {
            "enabled": True,
            "run_on_session_start": True,
            "min_confidence": 0.7
        },
        "spaced_repetition": {
            "enabled": True,
            "intervals_days": [1, 3, 7, 14, 30]
        },
        "recommendations": {
            "enabled": True,
            "max_suggestions": 5,
            "prefer_category": None
        },
        "ui": {
            "show_ai_summary": True,
            "progress_bar_style": "blocks",
            "max_recent_activities": 5
        }
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def update_session_count(progress: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aktualizuj licznik sesji i streak

    Args:
        progress: Dict z postępem

    Returns:
        Zaktualizowany Dict
    """
    progress["sessions"] = progress.get("sessions", 0) + 1

    last = progress.get("last_session")
    if last:
        try:
            last_date = datetime.fromisoformat(last).date()
            today = datetime.now().date()
            diff = (today - last_date).days

            if diff == 1:
                progress["streak_days"] += 1
            elif diff > 1:
                progress["streak_days"] = 1
        except ValueError:
            # Invalid date format
            progress["streak_days"] = 1
    else:
        progress["streak_days"] = 1

    progress["last_session"] = datetime.now().isoformat()

    return progress


def calculate_category_progress(concepts: Dict[str, Any], knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
    """
    Oblicz postęp w każdej kategorii na podstawie opanowanych konceptów

    Args:
        concepts: Dict z konceptami użytkownika (z progress)
        knowledge_base: Dict z bazą wiedzy

    Returns:
        Dict z postępem per kategoria
    """
    # TODO: Będzie rozbudowane gdy stworzymy knowledge_base
    return {}


def get_concepts_to_review(progress: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Znajdź koncepty do powtórki (spaced repetition)

    Args:
        progress: Dict z postępem
        config: Dict z konfiguracją (intervals)

    Returns:
        Lista konceptów do powtórki
    """
    if not config.get("spaced_repetition", {}).get("enabled", True):
        return []

    to_review = []
    intervals = config.get("spaced_repetition", {}).get("intervals_days", [1, 3, 7, 14, 30])

    # Convert intervals to dict: {mastery_level: days}
    intervals_dict = {i+1: days for i, days in enumerate(intervals)}

    for concept_id, data in progress.get("concepts", {}).items():
        level = data.get("mastery_level", 1)
        last_practiced = data.get("last_practiced")

        if not last_practiced:
            continue

        try:
            last_date = datetime.fromisoformat(last_practiced)
            days_interval = intervals_dict.get(level, intervals[0])
            days_ago = (datetime.now() - last_date).days

            if days_ago >= days_interval:
                to_review.append({
                    "id": concept_id,
                    "name": data.get("name", concept_id),
                    "level": level,
                    "days_ago": days_ago
                })
        except ValueError:
            # Invalid date format
            continue

    # Sortuj po days_ago (najdawniejsze pierwsze)
    to_review.sort(key=lambda x: x["days_ago"], reverse=True)

    return to_review[:3]  # Max 3


def format_concepts_for_review(concepts: List[Dict[str, Any]]) -> str:
    """
    Formatuj listę konceptów do wyświetlenia w review

    Args:
        concepts: Lista konceptów z get_concepts_to_review

    Returns:
        Sformatowany string
    """
    if not concepts:
        return "✅ Wszystko aktualne!"

    lines = []
    for c in concepts:
        emoji = "🟢" if c["level"] < 3 else "🟡" if c["level"] < 5 else "🔴"
        lines.append(f"  {emoji} **{c['name']}** (poziom {c['level']}, {c['days_ago']} dni temu)")

    return "\n".join(lines)


def ensure_data_files_exist():
    """Upewnij się że wszystkie wymagane pliki danych istnieją"""
    # learning_progress.json
    progress_file = DATA_DIR / "learning_progress.json"
    if not progress_file.exists():
        save_progress(_get_default_progress())

    # config.json
    config_file = DATA_DIR / "config.json"
    if not config_file.exists():
        save_config(_get_default_config())

    # practice_log.jsonl
    log_file = DATA_DIR / "practice_log.jsonl"
    if not log_file.exists():
        log_file.touch()

    logger.info("Data files initialized")


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    """Test data manager functions"""
    print("Testing data_manager.py...")

    # Ensure files exist
    ensure_data_files_exist()

    # Load
    progress = load_progress()
    config = load_config()
    kb = load_knowledge_base()
    logs = load_practice_log()

    print(f"\n✅ Progress loaded: {progress.get('sessions', 0)} sessions")
    print(f"✅ Config loaded: auto_tracking={config.get('auto_tracking', {}).get('enabled')}")
    print(f"✅ Knowledge base: {len(kb.get('concepts', {}))} concepts")
    print(f"✅ Practice log: {len(logs)} entries")

    # Update session
    progress = update_session_count(progress)
    save_progress(progress)
    print(f"\n✅ Session updated: #{progress['sessions']}, streak={progress['streak_days']}")
