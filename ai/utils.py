"""Utility functions for AI processing."""
import logging
from agents.mcp.server import MCPServerStdio
from utils.discord_utils import resolve_mentions, restore_mentions

logger = logging.getLogger(__name__)

def create_mcp_servers():
   """Create the configured MCP servers for the agents package.
   
   Returns:
       List: List of MCPServerStdio instances for the agents package
   """
   
   mcp_servers = []
   
   try:
       # Memory server (knowledge graph) - local stdio
       memory_server = MCPServerStdio(
           params={
               "command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-memory"],
               "env": {"MEMORY_FILE_PATH": "/data/memory.json"}
           },
           cache_tools_list=True  # Cache tools for performance
       )
       mcp_servers.append(memory_server)
       logger.info("Added memory MCP server")
   except Exception as e:
       logger.warning(f"Could not configure memory server: {e}")
   
   try:
       # Filesystem server - local stdio
       filesystem_server = MCPServerStdio(
           params={
               "command": "npx", 
               "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"]
           },
           cache_tools_list=True  # Cache tools for performance
       )
       mcp_servers.append(filesystem_server)
       logger.info("Added filesystem MCP server")
   except Exception as e:
       logger.warning(f"Could not configure filesystem server: {e}")
   
   try:
       # Sequential thinking server - local stdio
       thinking_server = MCPServerStdio(
           params={
               "command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
           },
           cache_tools_list=True  # Cache tools for performance
       )
       mcp_servers.append(thinking_server)
       logger.info("Added thinking MCP server")
   except Exception as e:
       logger.warning(f"Could not configure thinking server: {e}")
   
   logger.info(f"Configured {len(mcp_servers)} MCP servers")
   return mcp_servers
