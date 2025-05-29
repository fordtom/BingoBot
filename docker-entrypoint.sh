#!/bin/bash
set -e

# Debug: Show directory structure and permissions
echo "=== Debug: Current directory structure ==="
ls -la /

echo -e "\n=== Debug: Data directory ==="
ls -la /data 2>&1 || echo "Failed to list /data"

# Start the Python bot which will handle the MCP server
echo -e "\n=== Starting Discord bot with MCP client ==="
exec python -u bot.py > /data/bot.log 2>&1