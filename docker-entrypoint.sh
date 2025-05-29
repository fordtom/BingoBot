#!/bin/bash
set -e

# Debug: Show directory structure and permissions
echo "=== Debug: Current directory structure ==="
ls -la /

echo -e "\n=== Debug: Data directory ==="
ls -la /data 2>&1 || echo "Failed to list /data"

# Ensure data directory is writable
echo -e "\n=== Ensuring data directory permissions ==="
mkdir -p /data
chmod 755 /data
echo "Data directory permissions set"

# Start the Python bot which will handle the MCP server
echo -e "\n=== Starting Discord bot with MCP client ==="
exec python -u bot.py > /data/bot.log 2>&1