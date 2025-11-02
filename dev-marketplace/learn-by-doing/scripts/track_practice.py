#!/usr/bin/env python3
"""
PostToolUse Hook - Śledzi akcje użytkownika i loguje do practice_log

Enhanced (Universal Learning System v2.0):
- Import detection (Python files)
- Code analysis support
- Extended event types (quiz_result, learning_interaction)
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime

# Import data_manager for config loading
sys.path.insert(0, str(Path(__file__).parent))
from data_manager import load_config

PLUGIN_ROOT = Path(__file__).parent.parent
DATA_DIR = PLUGIN_ROOT / "data"
LOG_FILE = DATA_DIR / "practice_log.jsonl"

DATA_DIR.mkdir(exist_ok=True)

def categorize_action(tool_name, tool_input):
    """Kategoryzuj akcję użytkownika"""

    if tool_name == "Write":
        return "file_create"
    elif tool_name == "Edit" or tool_name == "StrReplace":
        return "file_edit"
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        if "pytest" in command:
            return "test_run"
        elif "git" in command:
            return "git_operation"
        else:
            return "bash_command"
    else:
        return "other"

def detect_imports_from_content(content: str, language: str = "python") -> list:
    """
    Wykryj importy z kodu

    Args:
        content: Treść pliku
        language: Język programowania

    Returns:
        Lista wykrytych bibliotek/modułów
    """
    imports = []

    if language == "python":
        # Match: import X, from X import Y
        import_patterns = [
            r'^import\s+([\w\.]+)',
            r'^from\s+([\w\.]+)\s+import',
        ]

        for line in content.split('\n'):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1).split('.')[0]  # Get root module
                    if module not in imports and not module.startswith('_'):
                        imports.append(module)

    return imports[:10]  # Limit to 10


def extract_context(tool_input):
    """Wyciągnij kontekst z tool_input (enhanced z import detection)"""

    file_path = tool_input.get("file_path") or tool_input.get("path")

    if not file_path:
        return {"type": "unknown"}

    path_obj = Path(file_path)
    file_name = path_obj.name
    file_ext = path_obj.suffix

    # Detect file type
    if "/services/" in file_path:
        file_type = "service"
    elif "/api/" in file_path:
        file_type = "api_endpoint"
    elif "/tests/" in file_path:
        file_type = "test"
    else:
        file_type = "other"

    context = {
        "type": file_type,
        "file": file_name,
        "language": None,
        "detected_libraries": []
    }

    # Detect language
    if file_ext == ".py":
        context["language"] = "python"
    elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
        context["language"] = "javascript"
    elif file_ext in [".rs"]:
        context["language"] = "rust"
    elif file_ext in [".go"]:
        context["language"] = "go"

    # Import detection (tylko dla Python na razie)
    if file_ext == ".py" and "content" in tool_input:
        content = tool_input.get("content", "")
        if content:
            imports = detect_imports_from_content(content, "python")
            if imports:
                context["detected_libraries"] = imports

    return context

def is_learning_moment(action, context):
    """Sprawdź czy to moment uczący"""

    if action in ["file_create", "file_edit"]:
        return True

    if action == "test_run":
        return True

    return False

def log_action(entry):
    """Zapisz akcję do logu"""

    try:
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️ Nie udało się zapisać logu: {e}", file=sys.stderr)

def main():
    """Główna funkcja PostToolUse hook"""

    try:
        # Check if plugin is enabled
        config = load_config()
        if not config.get("enabled", True):
            # Plugin is disabled - exit silently
            sys.exit(0)

        hook_data = json.loads(sys.stdin.read())

        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})

        action = categorize_action(tool_name, tool_input)
        context = extract_context(tool_input)

        if is_learning_moment(action, context):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "action": action,
                "context": context
            }

            log_action(entry)

        sys.exit(0)

    except Exception as e:
        print(f"⚠️ Błąd w track_practice: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
