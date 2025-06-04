#!/usr/bin/env bash
set -euo pipefail

# Mark repository as safe for Git when running as root
if [ "$(id -u)" -eq 0 ]; then
    git config --global --add safe.directory "$(pwd)"
fi

# Ensure uv package manager is installed
python -m pip install --no-cache-dir uv

# Create and activate virtual environment if missing
if [ ! -d ".venv" ]; then
    uv venv
fi
. .venv/bin/activate

# Install locked dependencies
uv sync --frozen

# Install pytest for running tests
uv pip install pytest

