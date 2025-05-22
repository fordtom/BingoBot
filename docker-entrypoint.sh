#!/bin/bash
set -e

# Start the MCP filesystem server in the background
echo "Starting MCP filesystem server..."
npx @modelcontextprotocol/server-filesystem /nas > /app/data/mcp-server.log 2>&1 &
MCP_PID=$!

# Give the MCP server time to start
sleep 2

# Check if MCP server is running
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "MCP server failed to start. Check /app/data/mcp-server.log for details."
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
exec python bot.py