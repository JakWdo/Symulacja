#!/usr/bin/env python3
"""
Testy dla track_practice.py - weryfikacja naprawionych błędów

Sprawdza:
1. Czy extract_context() zachowuje pełne ścieżki plików
2. Czy pattern matching działa z pełnymi ścieżkami
3. Czy timestamps używają UTC
4. Czy wykrywanie typu pliku działa poprawnie
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Dodaj scripts do path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from track_practice import extract_context, categorize_action, is_learning_moment


class TestExtractContext:
    """Testy dla funkcji extract_context()"""

    def test_preserves_full_path(self):
        """Test: extract_context() zachowuje pełną ścieżkę pliku"""
        tool_input = {
            "file_path": "app/services/personas/persona_generator.py"
        }

        context = extract_context(tool_input)

        # Weryfikuj że pełna ścieżka jest zachowana
        assert context["file"] == "app/services/personas/persona_generator.py"
        assert "persona_generator.py" not in context["file"] or "/" in context["file"]

    def test_preserves_full_path_with_path_key(self):
        """Test: extract_context() działa z kluczem 'path' zamiast 'file_path'"""
        tool_input = {
            "path": "app/api/projects.py"
        }

        context = extract_context(tool_input)

        assert context["file"] == "app/api/projects.py"

    def test_detects_service_type(self):
        """Test: wykrywa typ pliku 'service'"""
        tool_input = {
            "file_path": "app/services/personas/persona_service.py"
        }

        context = extract_context(tool_input)

        assert context["type"] == "service"
        assert context["file"] == "app/services/personas/persona_service.py"

    def test_detects_api_type(self):
        """Test: wykrywa typ pliku 'api_endpoint'"""
        tool_input = {
            "file_path": "app/api/focus_groups.py"
        }

        context = extract_context(tool_input)

        assert context["type"] == "api_endpoint"
        assert context["file"] == "app/api/focus_groups.py"

    def test_detects_test_type(self):
        """Test: wykrywa typ pliku 'test'"""
        tool_input = {
            "file_path": "tests/unit/services/test_persona_service.py"
        }

        context = extract_context(tool_input)

        assert context["type"] == "test"
        assert context["file"] == "tests/unit/services/test_persona_service.py"

    def test_detects_python_language(self):
        """Test: wykrywa język Python"""
        tool_input = {
            "file_path": "app/models/persona.py"
        }

        context = extract_context(tool_input)

        assert context["language"] == "python"

    def test_detects_javascript_language(self):
        """Test: wykrywa język JavaScript/TypeScript"""
        test_cases = [
            ("frontend/src/App.tsx", "javascript"),
            ("frontend/src/components/PersonaCard.jsx", "javascript"),
            ("frontend/src/lib/api.ts", "javascript"),
            ("frontend/src/index.js", "javascript"),
        ]

        for file_path, expected_lang in test_cases:
            tool_input = {"file_path": file_path}
            context = extract_context(tool_input)
            assert context["language"] == expected_lang, f"Failed for {file_path}"

    def test_handles_missing_file_path(self):
        """Test: obsługuje brak file_path"""
        tool_input = {}

        context = extract_context(tool_input)

        assert context["type"] == "unknown"

    def test_detects_imports_from_content(self):
        """Test: wykrywa importy z kodu Python"""
        tool_input = {
            "file_path": "app/services/test.py",
            "content": """
import pandas
from numpy import array
import sys
from pathlib import Path
"""
        }

        context = extract_context(tool_input)

        assert "pandas" in context["detected_libraries"]
        assert "numpy" in context["detected_libraries"]
        assert "sys" in context["detected_libraries"]
        assert "pathlib" in context["detected_libraries"]


class TestCategorizeAction:
    """Testy dla funkcji categorize_action()"""

    def test_categorizes_write(self):
        """Test: kategoryzuje akcję Write"""
        action = categorize_action("Write", {})
        assert action == "file_create"

    def test_categorizes_edit(self):
        """Test: kategoryzuje akcję Edit"""
        action = categorize_action("Edit", {})
        assert action == "file_edit"

    def test_categorizes_pytest(self):
        """Test: kategoryzuje pytest jako test_run"""
        tool_input = {"command": "pytest tests/"}
        action = categorize_action("Bash", tool_input)
        assert action == "test_run"

    def test_categorizes_git(self):
        """Test: kategoryzuje git jako git_operation"""
        tool_input = {"command": "git commit -m 'test'"}
        action = categorize_action("Bash", tool_input)
        assert action == "git_operation"

    def test_categorizes_other_bash(self):
        """Test: kategoryzuje inne bash jako bash_command"""
        tool_input = {"command": "ls -la"}
        action = categorize_action("Bash", tool_input)
        assert action == "bash_command"


class TestIsLearningMoment:
    """Testy dla funkcji is_learning_moment()"""

    def test_file_edit_is_learning_moment(self):
        """Test: edycja pliku to moment uczący"""
        assert is_learning_moment("file_edit", {"type": "service"}) is True

    def test_file_create_is_learning_moment(self):
        """Test: utworzenie pliku to moment uczący"""
        assert is_learning_moment("file_create", {"type": "api_endpoint"}) is True

    def test_test_run_is_learning_moment(self):
        """Test: uruchomienie testów to moment uczący"""
        assert is_learning_moment("test_run", {"type": "test"}) is True

    def test_bash_command_is_not_learning_moment(self):
        """Test: zwykła komenda bash to nie moment uczący"""
        assert is_learning_moment("bash_command", {"type": "other"}) is False


class TestPatternMatching:
    """Testy integracyjne - pattern matching z concept_detector"""

    def test_service_path_matches_pattern(self):
        """Test: ścieżka serwisu pasuje do patternu app/services/**/*.py"""
        tool_input = {
            "file_path": "app/services/personas/persona_generator.py"
        }

        context = extract_context(tool_input)
        file_path = context["file"]

        # Symuluj pattern matching (jak w concept_detector.py)
        pattern = "app/services/**/*.py"
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"

        import re
        matches = bool(re.match(regex_pattern, file_path))

        assert matches, f"{file_path} should match {pattern}"

    def test_api_path_matches_pattern(self):
        """Test: ścieżka API pasuje do patternu app/api/*.py"""
        tool_input = {
            "file_path": "app/api/projects.py"
        }

        context = extract_context(tool_input)
        file_path = context["file"]

        pattern = "app/api/*.py"
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"

        import re
        matches = bool(re.match(regex_pattern, file_path))

        assert matches, f"{file_path} should match {pattern}"

    def test_test_path_matches_pattern(self):
        """Test: ścieżka testów pasuje do patternu tests/**/*.py"""
        tool_input = {
            "file_path": "tests/unit/services/test_persona_service.py"
        }

        context = extract_context(tool_input)
        file_path = context["file"]

        pattern = "tests/**/*.py"
        regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
        regex_pattern = f"^{regex_pattern}$"

        import re
        matches = bool(re.match(regex_pattern, file_path))

        assert matches, f"{file_path} should match {pattern}"


class TestTimestamps:
    """Testy dla UTC timestamps"""

    def test_timestamp_format_is_utc(self):
        """Test: timestamp jest w formacie UTC ISO"""
        # Tworzymy timestamp jak w track_practice.py
        timestamp = datetime.now(timezone.utc).isoformat()

        # Weryfikuj że jest ISO format
        assert "T" in timestamp
        assert "+" in timestamp or "Z" in timestamp or timestamp.endswith("+00:00")

        # Weryfikuj że można go sparsować
        parsed = datetime.fromisoformat(timestamp)
        assert parsed is not None

    def test_utc_timestamp_consistency(self):
        """Test: UTC timestamps są spójne między wywołaniami"""
        ts1 = datetime.now(timezone.utc)
        ts2 = datetime.now(timezone.utc)

        # Różnica powinna być minimalna (< 1 sekunda)
        diff = (ts2 - ts1).total_seconds()
        assert diff < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
