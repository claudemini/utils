#!/bin/bash

# Memory management wrapper
# Usage: ./memory.sh [command] [args]

UTILS_DIR="$(dirname "$0")"
cd "$UTILS_DIR"

# Run with uv
/Users/claudemini/.local/bin/uv run python memory_manager.py "$@"