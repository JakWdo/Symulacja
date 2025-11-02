#!/bin/bash

# Znajdź PLUGIN_ROOT dynamicznie
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

# Uruchom Python
python3 "$PLUGIN_ROOT/scripts/session_start_simple.py"
