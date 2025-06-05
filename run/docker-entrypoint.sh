#!/bin/bash
set -e

# Ensure data directory is writable
echo "=== Setting up data directory ==="
mkdir -p /data
chmod 777 /data
echo "Data directory permissions set"

# Set memory file path for memory server
export MEMORY_FILE_PATH="/data/memory.json"

# Node.js settings for MCP server stability
export NODE_OPTIONS="--max-old-space-size=512 --no-deprecation"
export UV_THREADPOOL_SIZE=128
export NODE_ENV=production

# Disable Node.js timeouts and keep-alive settings
export MCP_SERVER_TIMEOUT=0
export NODE_TIMEOUT=0
export SOCKET_TIMEOUT=0

echo "=== Node.js environment configured for MCP server stability ==="
echo "NODE_OPTIONS: $NODE_OPTIONS"
echo "MCP_SERVER_TIMEOUT: $MCP_SERVER_TIMEOUT"

# Start the Python bot which will use OpenAI Agents SDK with local MCP servers
echo -e "\n=== Starting Discord bot with OpenAI Agents SDK ===" 
echo "MCP servers will be launched on-demand by the Agents SDK via stdio"
python -u bot.py
