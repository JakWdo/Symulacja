#!/usr/bin/env python3
"""
Testy dla log_rotator.py - weryfikacja archiwizacji logów

Sprawdza:
1. Czy rotacja działa przy przekroczeniu limitu
2. Czy archiwa są tworzone poprawnie
3. Czy najnowsze wpisy są zachowywane
4. Czy statystyki są poprawnie obliczane
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import shutil

# Dodaj scripts do path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from log_rotator import LogRotator, rotate_practice_log


@pytest.fixture
def temp_data_dir():
    """Fixture: tymczasowy katalog danych dla testów"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_log_entries():
    """Fixture: przykładowe wpisy do logów"""
    entries = []
    for i in range(150):
        entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": "Edit",
            "action": "file_edit",
            "context": {
                "type": "service",
                "file": f"app/services/test_service_{i}.py"
            }
        })
    return entries


class TestLogRotator:
    """Testy dla klasy LogRotator"""

    def test_creates_archive_directory(self, temp_data_dir):
        """Test: tworzy katalog archives przy inicjalizacji"""
        rotator = LogRotator(temp_data_dir, max_entries=100)

        assert (temp_data_dir / "archives").exists()
        assert (temp_data_dir / "archives").is_dir()

    def test_loads_empty_log(self, temp_data_dir):
        """Test: ładuje pusty log bez błędów"""
        rotator = LogRotator(temp_data_dir)

        entries = rotator.load_log_entries()

        assert entries == []

    def test_saves_and_loads_entries(self, temp_data_dir, sample_log_entries):
        """Test: zapisuje i wczytuje wpisy poprawnie"""
        rotator = LogRotator(temp_data_dir)

        # Zapisz 10 wpisów
        test_entries = sample_log_entries[:10]
        success = rotator.save_log_entries(test_entries)

        assert success is True

        # Wczytaj i zweryfikuj
        loaded = rotator.load_log_entries()

        assert len(loaded) == 10
        assert loaded[0]["tool"] == "Edit"
        assert loaded[0]["action"] == "file_edit"

    def test_rotation_not_needed_when_under_limit(self, temp_data_dir):
        """Test: rotacja nie jest wykonywana gdy wpisy < limit"""
        rotator = LogRotator(temp_data_dir, max_entries=100)

        # Zapisz 50 wpisów (poniżej limitu 100)
        test_entries = []
        for i in range(50):
            test_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py"}
            })

        rotator.save_log_entries(test_entries)

        # Wykonaj rotację
        result = rotator.rotate_if_needed()

        assert result is True

        # Sprawdź że wszystkie wpisy są nadal w logu
        entries = rotator.load_log_entries()
        assert len(entries) == 50

        # Sprawdź że nie ma plików archiwum
        archive_files = list((temp_data_dir / "archives").glob("*.jsonl"))
        assert len(archive_files) == 0

    def test_rotation_when_limit_exceeded(self, temp_data_dir):
        """Test: rotacja działa gdy wpisy > limit"""
        rotator = LogRotator(temp_data_dir, max_entries=100)

        # Zapisz 150 wpisów (powyżej limitu 100)
        test_entries = []
        for i in range(150):
            test_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py", "index": i}
            })

        rotator.save_log_entries(test_entries)

        # Wykonaj rotację
        result = rotator.rotate_if_needed()

        assert result is True

        # Sprawdź że tylko 100 najnowszych wpisów jest w logu
        entries = rotator.load_log_entries()
        assert len(entries) == 100

        # Sprawdź że najnowsze wpisy zostały zachowane
        # Indeksy powinny być od 50 do 149 (ostatnie 100)
        assert entries[0]["context"]["index"] == 50
        assert entries[-1]["context"]["index"] == 149

        # Sprawdź że plik archiwum został utworzony
        archive_files = list((temp_data_dir / "archives").glob("practice_log_archive_*.jsonl"))
        assert len(archive_files) == 1

    def test_archive_file_contains_old_entries(self, temp_data_dir):
        """Test: plik archiwum zawiera stare wpisy"""
        rotator = LogRotator(temp_data_dir, max_entries=100)

        # Zapisz 150 wpisów
        test_entries = []
        for i in range(150):
            test_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py", "index": i}
            })

        rotator.save_log_entries(test_entries)
        rotator.rotate_if_needed()

        # Sprawdź zawartość archiwum
        archive_files = list((temp_data_dir / "archives").glob("practice_log_archive_*.jsonl"))
        assert len(archive_files) == 1

        archive_file = archive_files[0]
        archived_entries = []

        with archive_file.open('r', encoding='utf-8') as f:
            for line in f:
                archived_entries.append(json.loads(line))

        # Powinno być 50 starych wpisów (0-49)
        assert len(archived_entries) == 50
        assert archived_entries[0]["context"]["index"] == 0
        assert archived_entries[-1]["context"]["index"] == 49

    def test_archive_file_naming(self, temp_data_dir):
        """Test: nazwa pliku archiwum zawiera datę"""
        rotator = LogRotator(temp_data_dir, max_entries=10)

        # Zapisz 20 wpisów
        test_entries = []
        for i in range(20):
            test_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py"}
            })

        rotator.save_log_entries(test_entries)
        rotator.rotate_if_needed()

        # Sprawdź nazwę pliku archiwum
        archive_files = list((temp_data_dir / "archives").glob("practice_log_archive_*.jsonl"))
        assert len(archive_files) == 1

        archive_file = archive_files[0]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        assert f"practice_log_archive_{today}.jsonl" == archive_file.name

    def test_get_stats(self, temp_data_dir):
        """Test: statystyki są poprawnie obliczane"""
        rotator = LogRotator(temp_data_dir, max_entries=100)

        # Zapisz 150 wpisów i zrób rotację
        test_entries = []
        for i in range(150):
            test_entries.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py"}
            })

        rotator.save_log_entries(test_entries)
        rotator.rotate_if_needed()

        # Pobierz statystyki
        stats = rotator.get_stats()

        assert stats["current_entries"] == 100
        assert stats["max_entries"] == 100
        assert stats["needs_rotation"] is False
        assert stats["archive_files"] == 1
        assert stats["total_archived"] == 50
        assert stats["total_entries"] == 150

    def test_multiple_rotations(self, temp_data_dir):
        """Test: wiele rotacji dodaje do tego samego archiwum"""
        rotator = LogRotator(temp_data_dir, max_entries=50)

        # Pierwsza partia: 100 wpisów
        for i in range(100):
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Edit",
                "action": "file_edit",
                "context": {"file": f"test_{i}.py", "batch": 1}
            }
            rotator.save_log_entries(rotator.load_log_entries() + [entry])

        rotator.rotate_if_needed()

        # Druga partia: dodaj kolejne 60 wpisów
        for i in range(60):
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": "Write",
                "action": "file_create",
                "context": {"file": f"new_{i}.py", "batch": 2}
            }
            rotator.save_log_entries(rotator.load_log_entries() + [entry])

        rotator.rotate_if_needed()

        # Sprawdź że jest tylko jeden plik archiwum (ten sam dzień)
        archive_files = list((temp_data_dir / "archives").glob("practice_log_archive_*.jsonl"))
        assert len(archive_files) == 1

        # Sprawdź że archiwum zawiera wpisy z obu batch'y
        with archive_files[0].open('r', encoding='utf-8') as f:
            archived = [json.loads(line) for line in f]

        # Powinno być 50 (z pierwszej) + 60 (z drugiej) = 110 wpisów
        assert len(archived) == 110


class TestRotatePracticeLogFunction:
    """Testy dla funkcji helper rotate_practice_log()"""

    def test_rotate_practice_log_function(self, temp_data_dir):
        """Test: funkcja helper działa poprawnie"""
        # Zapisz 150 wpisów
        log_file = temp_data_dir / "practice_log.jsonl"

        with log_file.open('w', encoding='utf-8') as f:
            for i in range(150):
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tool": "Edit",
                    "action": "file_edit",
                    "context": {"file": f"test_{i}.py"}
                }
                f.write(json.dumps(entry) + '\n')

        # Wykonaj rotację przez funkcję helper
        result = rotate_practice_log(temp_data_dir, max_entries=100)

        assert result is True

        # Sprawdź wynik
        rotator = LogRotator(temp_data_dir)
        entries = rotator.load_log_entries()

        assert len(entries) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
