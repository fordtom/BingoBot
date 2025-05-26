#!/bin/bash
set -e

# Debug: Show directory structure and permissions
echo "=== Debug: Current directory structure ==="
ls -la /

echo -e "\n=== Debug: NAS mount point ==="
ls -la /nas 2>&1 || echo "Failed to list /nas"

echo -e "\n=== Debug: App data directory ==="
ls -la /app/data

# Start the MCP filesystem server in the background
echo -e "\n=== Starting MCP filesystem server ==="
echo "Serving directories: /nas (read-only), /app/data (read-write)"

npx @modelcontextprotocol/server-filesystem /app/nas /app/data > /app/data/mcp-server.log 2>&1 &
MCP_PID=$!

# Give the MCP server time to start
sleep 2

# Check if MCP server is running
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "MCP server failed to start. Check /app/data/mcp-server.log for details."
    echo "=== MCP Server Log ==="
    cat /app/data/mcp-server.log || echo "No log file found"
    exit 1
fi

echo "MCP filesystem server started with PID $MCP_PID"

# Function to cleanup on exit
cleanup() {
    echo "Shutting down MCP server..."
    kill $MCP_PID 2>/dev/null || true
    wait $MCP_PID 2>/dev/null || true
    echo "MCP server stopped."
}

# Set up trap to cleanup on exit
trap cleanup EXIT INT TERM

# Start the Python bot
echo "Starting Discord bot..."
exec python -u bot.py > /app/data/bot.log 2>&1