#!/bin/bash
set -e

# Debug: Show directory structure and permissions
echo "=== Debug: Current directory structure ==="
ls -la /

echo -e "\n=== Debug: NAS mount point ==="
ls -la /nas 2>&1 || echo "Failed to list /nas"

echo -e "\n=== Debug: App data directory ==="
ls -la /app/data

# Start the Python bot which will handle the MCP server
echo -e "\n=== Starting Discord bot with MCP client ==="
exec python -u bot.py > /app/data/bot.log 2>&1