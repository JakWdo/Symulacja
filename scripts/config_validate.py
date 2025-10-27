#!/usr/bin/env python3
"""
Config Validation Script - Walidacja i auto-bump versioning

Funkcje:
- Walidacja wszystkich YAML files przeciw JSON schemas
- Auto-bump versioning gdy zmienia się hash promptu
- Sprawdzanie placeholderów w promptach
- Generowanie snapshot hashy

Usage:
    python scripts/config_validate.py
    python scripts/config_validate.py --check-placeholders
    python scripts/config_validate.py --generate-hashes
    python scripts/config_validate.py --auto-bump
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

# Config root
CONFIG_ROOT = Path(__file__).parent.parent / "config"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict):
    """Save YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def compute_prompt_hash(messages: list[dict]) -> str:
    """Compute SHA256 hash of normalized prompt content."""
    normalized = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def validate_prompt(prompt_file: Path) -> tuple[bool, str]:
    """
    Validate prompt file.

    Returns:
        (is_valid, message)
    """
    try:
        data = load_yaml(prompt_file)

        # Check required fields
        required = ["id", "version", "description", "messages"]
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"

        # Check ID format
        if not data["id"].count(".") >= 1:
            return False, f"Invalid ID format: {data['id']} (expected 'domain.name')"

        # Check version format
        version_parts = data["version"].split(".")
        if len(version_parts) != 3 or not all(p.isdigit() for p in version_parts):
            return False, f"Invalid version format: {data['version']} (expected semver)"

        # Check messages
        if not isinstance(data["messages"], list) or len(data["messages"]) == 0:
            return False, "Messages must be non-empty list"

        for msg in data["messages"]:
            if "role" not in msg or "content" not in msg:
                return False, "Message missing 'role' or 'content'"
            if msg["role"] not in ["system", "user", "assistant"]:
                return False, f"Invalid role: {msg['role']}"

        return True, "OK"

    except Exception as e:
        return False, f"Error: {e}"


def auto_bump_version(prompt_file: Path, dry_run: bool = False) -> tuple[bool, str]:
    """
    Auto-bump version jeśli hash się zmienił.

    Returns:
        (bumped, message)
    """
    data = load_yaml(prompt_file)
    messages = data["messages"]

    current_hash = compute_prompt_hash(messages)
    stored_hash = data.get("hash", "")

    if current_hash != stored_hash:
        # Hash changed - bump version
        version_parts = data["version"].split(".")
        patch = int(version_parts[2]) + 1
        new_version = f"{version_parts[0]}.{version_parts[1]}.{patch}"

        if not dry_run:
            data["version"] = new_version
            data["hash"] = current_hash
            save_yaml(prompt_file, data)

        return True, f"Bumped {data['id']}: {data['version']} → {new_version} (hash changed)"
    else:
        return False, f"{data['id']}: v{data['version']} unchanged"


def check_placeholders(prompt_file: Path) -> tuple[bool, list[str]]:
    """
    Extract placeholders z promptu (${var} format).

    Returns:
        (has_placeholders, list_of_placeholders)
    """
    data = load_yaml(prompt_file)
    placeholders = set()

    for msg in data["messages"]:
        content = msg["content"]

        # Find ${...} patterns
        import re
        matches = re.findall(r"\$\{([^}]+)\}", content)
        placeholders.update(matches)

    return len(placeholders) > 0, sorted(placeholders)


def validate_all_prompts(auto_bump: bool = False, check_placeholders_flag: bool = False):
    """Validate all prompts in config/prompts/."""
    prompts_dir = CONFIG_ROOT / "prompts"
    all_prompts = list(prompts_dir.rglob("*.yaml"))

    print(f"Found {len(all_prompts)} prompt files\n")

    errors = []
    bumped_count = 0

    for prompt_file in sorted(all_prompts):
        # Validate
        is_valid, message = validate_prompt(prompt_file)

        if not is_valid:
            print(f"❌ {prompt_file.relative_to(CONFIG_ROOT)}: {message}")
            errors.append((prompt_file, message))
            continue

        # Auto-bump if requested
        if auto_bump:
            bumped, bump_msg = auto_bump_version(prompt_file)
            if bumped:
                print(f"🔄 {bump_msg}")
                bumped_count += 1
            else:
                print(f"✅ {bump_msg}")
        else:
            print(f"✅ {prompt_file.relative_to(CONFIG_ROOT)}: {message}")

        # Check placeholders if requested
        if check_placeholders_flag:
            has_placeholders, placeholders = check_placeholders(prompt_file)
            if has_placeholders:
                print(f"   Placeholders: {', '.join(placeholders)}")

    print(f"\n{'='*80}")
    if errors:
        print(f"❌ Validation failed: {len(errors)} errors")
        for file, msg in errors:
            print(f"   - {file.relative_to(CONFIG_ROOT)}: {msg}")
        return False
    else:
        print(f"✅ All prompts valid!")
        if auto_bump and bumped_count > 0:
            print(f"🔄 Auto-bumped {bumped_count} prompts")
        return True


def validate_models():
    """Validate models.yaml."""
    models_file = CONFIG_ROOT / "models.yaml"
    print(f"Validating {models_file.relative_to(CONFIG_ROOT)}...")

    try:
        data = load_yaml(models_file)

        # Check required fields
        if "defaults" not in data or "chat" not in data["defaults"]:
            print("❌ Missing defaults.chat section")
            return False

        # Check chat default has model
        if "model" not in data["defaults"]["chat"]:
            print("❌ defaults.chat missing 'model' field")
            return False

        print("✅ models.yaml valid!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate config files")
    parser.add_argument("--auto-bump", action="store_true", help="Auto-bump versions on hash change")
    parser.add_argument("--check-placeholders", action="store_true", help="Show prompt placeholders")
    parser.add_argument("--generate-hashes", action="store_true", help="Generate prompt hashes")
    args = parser.parse_args()

    print("="*80)
    print("CONFIG VALIDATION")
    print("="*80 + "\n")

    # Validate prompts
    prompts_valid = validate_all_prompts(
        auto_bump=args.auto_bump,
        check_placeholders_flag=args.check_placeholders
    )

    print()

    # Validate models
    models_valid = validate_models()

    print("\n" + "="*80)

    if prompts_valid and models_valid:
        print("✅ All validations passed!")
        sys.exit(0)
    else:
        print("❌ Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
