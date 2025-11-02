#!/usr/bin/env python3
"""
Log Rotator - Automatyczna archiwizacja practice_log.jsonl

Funkcjonalność:
- Sprawdza rozmiar practice_log.jsonl
- Przy przekroczeniu limitu przenosi stare wpisy do archiwum
- Archiwum: practice_log_archive_YYYY-MM-DD.jsonl
- Zachowuje tylko najnowsze wpisy w głównym logu

Universal Learning System v2.0
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogRotator:
    """Zarządzanie rotacją practice log"""

    def __init__(self, data_dir: Path, max_entries: int = 1000):
        """
        Args:
            data_dir: Katalog z danymi pluginu
            max_entries: Maksymalna liczba wpisów w practice_log.jsonl
        """
        self.data_dir = data_dir
        self.max_entries = max_entries
        self.log_file = data_dir / "practice_log.jsonl"
        self.archive_dir = data_dir / "archives"

        # Utwórz katalog archiwów
        self.archive_dir.mkdir(exist_ok=True)

    def load_log_entries(self) -> List[Dict[str, Any]]:
        """Wczytaj wszystkie wpisy z practice_log.jsonl"""
        if not self.log_file.exists():
            return []

        entries = []
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error loading log entries: {e}")
            return []

        return entries

    def save_log_entries(self, entries: List[Dict[str, Any]]) -> bool:
        """Zapisz wpisy do practice_log.jsonl"""
        try:
            with self.log_file.open('w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            logger.error(f"Error saving log entries: {e}")
            return False

    def archive_old_entries(self, entries: List[Dict[str, Any]]) -> bool:
        """
        Archiwizuj stare wpisy do pliku archiwum

        Args:
            entries: Lista wpisów do zarchiwizowania

        Returns:
            True jeśli sukces
        """
        if not entries:
            return True

        # Nazwa pliku archiwum z datą
        archive_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive_file = self.archive_dir / f"practice_log_archive_{archive_date}.jsonl"

        try:
            # Jeśli plik istnieje, dopisz do niego
            mode = 'a' if archive_file.exists() else 'w'

            with archive_file.open(mode, encoding='utf-8') as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')

            logger.info(f"Archived {len(entries)} entries to {archive_file.name}")
            return True

        except Exception as e:
            logger.error(f"Error archiving entries: {e}")
            return False

    def rotate_if_needed(self) -> bool:
        """
        Sprawdź czy potrzebna rotacja i wykonaj ją jeśli tak

        Returns:
            True jeśli rotacja wykonana lub nie była potrzebna
        """
        entries = self.load_log_entries()

        if len(entries) <= self.max_entries:
            # Rotacja nie jest potrzebna
            return True

        logger.info(f"Log rotation needed: {len(entries)} entries (limit: {self.max_entries})")

        # Oblicz ile wpisów przenieść do archiwum
        num_to_archive = len(entries) - self.max_entries

        # Podziel na stare (do archiwum) i nowe (zachować)
        old_entries = entries[:num_to_archive]
        new_entries = entries[num_to_archive:]

        # Archiwizuj stare wpisy
        if not self.archive_old_entries(old_entries):
            logger.error("Failed to archive old entries")
            return False

        # Zapisz tylko nowe wpisy do głównego logu
        if not self.save_log_entries(new_entries):
            logger.error("Failed to save new entries")
            return False

        logger.info(f"Log rotation complete: kept {len(new_entries)} entries, archived {len(old_entries)}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Pobierz statystyki logów

        Returns:
            Dict z informacjami o logach i archiwach
        """
        entries = self.load_log_entries()

        # Zlicz pliki archiwum
        archive_files = list(self.archive_dir.glob("practice_log_archive_*.jsonl"))
        total_archived = 0

        for archive_file in archive_files:
            try:
                with archive_file.open('r', encoding='utf-8') as f:
                    total_archived += sum(1 for _ in f)
            except Exception as e:
                logger.warning(f"Error counting archive {archive_file.name}: {e}")

        return {
            "current_entries": len(entries),
            "max_entries": self.max_entries,
            "needs_rotation": len(entries) > self.max_entries,
            "archive_files": len(archive_files),
            "total_archived": total_archived,
            "total_entries": len(entries) + total_archived
        }


def rotate_practice_log(data_dir: Path, max_entries: int = 1000) -> bool:
    """
    Helper function - rotacja practice log

    Args:
        data_dir: Katalog z danymi
        max_entries: Maksymalna liczba wpisów

    Returns:
        True jeśli sukces
    """
    rotator = LogRotator(data_dir, max_entries)
    return rotator.rotate_if_needed()


if __name__ == "__main__":
    """Testowanie - uruchom rotację ręcznie"""
    from pathlib import Path

    # Znajdź katalog danych
    plugin_root = Path(__file__).parent.parent
    data_dir = plugin_root / "data"

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        exit(1)

    # Stwórz rotator i wyświetl statystyki
    rotator = LogRotator(data_dir, max_entries=1000)

    print("\n📊 Log Statistics:")
    stats = rotator.get_stats()
    print(f"  Current entries: {stats['current_entries']}")
    print(f"  Max entries: {stats['max_entries']}")
    print(f"  Needs rotation: {stats['needs_rotation']}")
    print(f"  Archive files: {stats['archive_files']}")
    print(f"  Total archived: {stats['total_archived']}")
    print(f"  Total entries: {stats['total_entries']}")

    # Wykonaj rotację jeśli potrzebna
    if stats['needs_rotation']:
        print("\n🔄 Performing log rotation...")
        if rotator.rotate_if_needed():
            print("✅ Log rotation successful")

            # Wyświetl nowe statystyki
            new_stats = rotator.get_stats()
            print(f"\n📊 After rotation:")
            print(f"  Current entries: {new_stats['current_entries']}")
            print(f"  Archive files: {new_stats['archive_files']}")
            print(f"  Total archived: {new_stats['total_archived']}")
        else:
            print("❌ Log rotation failed")
    else:
        print("\n✅ No rotation needed")
