#!/usr/bin/env python3
"""
PostToolUse Hook - Śledzi akcje użytkownika i loguje do practice_log
"""
import json
import sys
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

def extract_context(tool_input):
    """Wyciągnij kontekst z tool_input"""

    if "path" in tool_input:
        path = tool_input["path"]

        if "/services/" in path:
            return {"type": "service", "file": Path(path).name}
        elif "/api/" in path:
            return {"type": "api_endpoint", "file": Path(path).name}
        elif "/tests/" in path:
            return {"type": "test", "file": Path(path).name}
        else:
            return {"type": "other", "file": Path(path).name}

    if "file_path" in tool_input:
        path = tool_input["file_path"]

        if "/services/" in path:
            return {"type": "service", "file": Path(path).name}
        elif "/api/" in path:
            return {"type": "api_endpoint", "file": Path(path).name}
        elif "/tests/" in path:
            return {"type": "test", "file": Path(path).name}
        else:
            return {"type": "other", "file": Path(path).name}

    return {"type": "unknown"}

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
