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
chmod 777 /data
echo "Data directory permissions set"

# Set memory file path for memory server
export MEMORY_FILE_PATH="/data/memory.json"

# Test MCP servers are available
echo -e "\n=== Testing MCP server availability ==="
echo "Testing memory server..."
npx -y @modelcontextprotocol/server-memory --help >/dev/null 2>&1 && echo "Memory server available" || echo "Memory server not available"

echo "Testing filesystem server..."
npx -y @modelcontextprotocol/server-filesystem --help >/dev/null 2>&1 && echo "Filesystem server available" || echo "Filesystem server not available"

echo "Testing thinking server..."
npx -y @modelcontextprotocol/server-sequential-thinking --help >/dev/null 2>&1 && echo "Thinking server available" || echo "Thinking server not available"

# Start the Python bot which will use OpenAI Agents SDK with local MCP servers
echo -e "\n=== Starting Discord bot with OpenAI Agents SDK ===" 
echo "MCP servers will be launched on-demand by the Agents SDK via stdio"
python -u bot.py 2>&1 | tee /data/bot.log