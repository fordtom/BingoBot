#!/bin/bash

echo "=== Bot Log ==="
if [ -f "./data/bot.log" ]; then
    tail -n 50 ./data/bot.log
else
    echo "No bot.log found"
fi

echo -e "\n=== MCP Server Log ==="
if [ -f "./data/mcp-server.log" ]; then
    tail -n 50 ./data/mcp-server.log
else
    echo "No mcp-server.log found"
fi

echo -e "\n=== Docker Container Logs ==="
docker-compose logs --tail 50
