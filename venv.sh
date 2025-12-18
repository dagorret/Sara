#!/usr/bin/env bash

VENV_DIR=".venv"

activate() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "❌ Virtual environment not found at $VENV_DIR"
        echo "Create it with: uv venv .venv"
        return 1
    fi

    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
}

deactivate_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "ℹ️ No virtual environment is currently active"
        return 0
    fi

    deactivate
    echo "✅ Virtual environment deactivated"
}

case "$1" in
    d|deactivate)
        deactivate_venv
        ;;
    *)
        activate
        ;;
esac
