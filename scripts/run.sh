#!/usr/bin/env bash
# Launches Cat & Sage on Linux/macOS (also works under Git Bash on Windows).
#
# Creates the local virtualenv on first run (installing the project in
# editable mode with dev extras), seeds .env from .env.example if missing,
# then forwards all arguments to `python -m cat_sage.cli`.
#
# Usage:
#   scripts/run.sh "Why is the sky blue?"
#   scripts/run.sh                # prompts interactively when no question is given

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT/.venv"

# POSIX venvs use bin/python; venvs created by Windows python.exe (e.g. via
# Git Bash) use Scripts/python.exe -- support either.
find_venv_python() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        echo "$VENV_DIR/bin/python"
    elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
        echo "$VENV_DIR/Scripts/python.exe"
    fi
}

VENV_PYTHON="$(find_venv_python || true)"

if [ -z "$VENV_PYTHON" ]; then
    echo "No virtualenv found -- creating one at $VENV_DIR ..."
    PY="$(command -v python3 || command -v python)"
    "$PY" -m venv "$VENV_DIR"
    VENV_PYTHON="$(find_venv_python)"
    "$VENV_PYTHON" -m pip install --quiet --upgrade pip
    "$VENV_PYTHON" -m pip install --quiet -e "$ROOT[dev]"
fi

if [ ! -f "$ROOT/.env" ] && [ -f "$ROOT/.env.example" ]; then
    echo "No .env found -- copying .env.example -> .env"
    cp "$ROOT/.env.example" "$ROOT/.env"
fi

exec "$VENV_PYTHON" -m cat_sage.cli "$@"
