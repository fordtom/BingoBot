#!/bin/bash
set -e

# Ensure data directory is writable
echo "=== Setting up data directory ==="
mkdir -p /data
chmod 777 /data
echo "Data directory permissions set"

# Set memory file path for memory server
export MEMORY_FILE_PATH="/data/memory.json"

# Start the Python bot which will use OpenAI Agents SDK with local MCP servers
echo -e "\n=== Starting Discord bot with OpenAI Agents SDK ===" 
echo "MCP servers will be launched on-demand by the Agents SDK via stdio"
python -u bot.py 2>&1 | tee /data/bot.log
