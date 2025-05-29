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

# Start MCP servers via HTTP proxy
echo -e "\n=== Starting MCP servers via HTTP proxy ==="

# Set memory file path for memory server
export MEMORY_FILE_PATH="/data/memory.json"

# Start memory server on port 3001
echo "Starting memory server on port 3001..."
mcp-remote --stdio "npx -y @modelcontextprotocol/server-memory" --port 3001 &
MEMORY_PID=$!

# Start filesystem server on port 3002  
echo "Starting filesystem server on port 3002..."
mcp-remote --stdio "npx -y @modelcontextprotocol/server-filesystem /data" --port 3002 &
FILESYSTEM_PID=$!

# Start sequential thinking server on port 3003
echo "Starting sequential thinking server on port 3003..."
mcp-remote --stdio "npx -y @modelcontextprotocol/server-sequential-thinking" --port 3003 &
THINKING_PID=$!

# Give servers time to start
sleep 3

# Function to cleanup background processes
cleanup() {
    echo "Shutting down MCP servers..."
    kill $MEMORY_PID $FILESYSTEM_PID $THINKING_PID 2>/dev/null || true
    wait
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

echo "MCP servers started. PIDs: Memory=$MEMORY_PID, Filesystem=$FILESYSTEM_PID, Thinking=$THINKING_PID"

# Start the Python bot which will use native OpenAI MCP integration
echo -e "\n=== Starting Discord bot with native MCP integration ==="
python -u bot.py 2>&1 | tee /data/bot.log