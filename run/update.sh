#!/usr/bin/env bash
set -euo pipefail

# Navigate to repository root (parent directory of this script)
cd "$(dirname "$0")/.."

# Fetch updates from the remote master branch
# Assumes remote is named 'origin'
git fetch origin master

# Check if local HEAD differs from origin/master
if ! git diff --quiet HEAD origin/master; then
    git pull origin master
    docker compose up -d --build
fi

