#!/bin/bash

echo "=== Bot Debug Log ==="
if [ -f "./data/bot-debug.log" ]; then
    tail -n 50 ./data/bot-debug.log
else
    echo "No bot-debug.log found"
fi

echo -e "\n=== Bot Output Log ==="
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