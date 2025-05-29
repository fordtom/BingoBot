"""MCP client for connecting to MCP servers."""
import asyncio
import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPClient:
   """Client for interacting with multiple MCP servers."""
   
   def __init__(self):
      self.filesystem_session = None
      self.memory_session = None
      self.sequential_thinking_session = None
      self.tools = []
      self.exit_stack = None
      self.filesystem_stdio = None
      self.filesystem_write = None
      self.memory_stdio = None
      self.memory_write = None
      self.sequential_thinking_stdio = None
      self.sequential_thinking_write = None
      
   async def connect(self):
      """Connect to all MCP servers (filesystem, memory, and sequential-thinking)."""
      try:
         # Initialize exit stack
         self.exit_stack = AsyncExitStack()
         
         # Connect to all servers
         filesystem_success = await self._connect_filesystem()
         memory_success = await self._connect_memory()
         sequential_thinking_success = await self._connect_sequential_thinking()
         
         # Collect all tools from all servers
         all_tools = []
         if self.filesystem_session:
            try:
               tools_response = await self.filesystem_session.list_tools()
               all_tools.extend(tools_response.tools)
               logger.info(f"Filesystem tools: {[t.name for t in tools_response.tools]}")
            except Exception as e:
               logger.warning(f"Failed to get filesystem tools: {e}")
         
         if self.memory_session:
            try:
               tools_response = await self.memory_session.list_tools()
               all_tools.extend(tools_response.tools)
               logger.info(f"Memory tools: {[t.name for t in tools_response.tools]}")
            except Exception as e:
               logger.warning(f"Failed to get memory tools: {e}")
         
         if self.sequential_thinking_session:
            try:
               tools_response = await self.sequential_thinking_session.list_tools()
               all_tools.extend(tools_response.tools)
               logger.info(f"Sequential thinking tools: {[t.name for t in tools_response.tools]}")
            except Exception as e:
               logger.warning(f"Failed to get sequential thinking tools: {e}")
         
         self.tools = all_tools
         
         if not self.tools:
            logger.warning("No tools found from any MCP server")
            return False
            
         logger.info(f"Connected to MCP servers. Available tools: {[t.name for t in self.tools]}")
         return filesystem_success or memory_success or sequential_thinking_success
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP servers: {e}")
         return False
   
   async def _connect_filesystem(self):
      """Connect to the filesystem MCP server."""
      try:
         logger.info("Starting MCP filesystem server...")
         
         # Create server parameters for the filesystem server
         filesystem_params = StdioServerParameters(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-filesystem', '/data'],
            env=None
         )
         
         logger.info("Creating stdio transport for filesystem MCP server...")
         
         # Create stdio transport using server parameters
         filesystem_transport = await self.exit_stack.enter_async_context(
            stdio_client(filesystem_params)
         )
         
         # Get the stdio streams
         self.filesystem_stdio, self.filesystem_write = filesystem_transport
         
         logger.info("Creating filesystem MCP client session...")
         self.filesystem_session = await self.exit_stack.enter_async_context(
            ClientSession(self.filesystem_stdio, self.filesystem_write)
         )
         
         # Initialize the session
         logger.info("Initializing filesystem MCP session...")
         await self.filesystem_session.initialize()
         
         logger.info("Successfully connected to filesystem MCP server")
         return True
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP filesystem server: {e}")
         return False
   
   async def _connect_memory(self):
      """Connect to the memory MCP server."""
      try:
         logger.info("Starting MCP memory server...")
         
         # Set memory file path - use data directory
         memory_file_path = '/data/memory.json'
         
         # Create server parameters for the memory server with explicit environment
         memory_env = os.environ.copy()
         memory_env['MEMORY_FILE_PATH'] = memory_file_path
         
         memory_params = StdioServerParameters(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-memory'],
            env=memory_env
         )
         
         logger.info(f"Creating stdio transport for memory MCP server (file: {memory_file_path})...")
         
         # Create stdio transport using server parameters
         memory_transport = await self.exit_stack.enter_async_context(
            stdio_client(memory_params)
         )
         
         # Get the stdio streams
         self.memory_stdio, self.memory_write = memory_transport
         
         logger.info("Creating memory MCP client session...")
         self.memory_session = await self.exit_stack.enter_async_context(
            ClientSession(self.memory_stdio, self.memory_write)
         )
         
         # Initialize the session
         logger.info("Initializing memory MCP session...")
         await self.memory_session.initialize()
         
         logger.info("Successfully connected to memory MCP server")
         return True
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP memory server: {e}")
         return False
   
   async def _connect_sequential_thinking(self):
      """Connect to the sequential-thinking MCP server."""
      try:
         logger.info("Starting MCP sequential-thinking server...")
         
         # Create server parameters for the sequential-thinking server
         sequential_thinking_params = StdioServerParameters(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-sequential-thinking'],
            env=None
         )
         
         logger.info("Creating stdio transport for sequential-thinking MCP server...")
         
         # Create stdio transport using server parameters
         sequential_thinking_transport = await self.exit_stack.enter_async_context(
            stdio_client(sequential_thinking_params)
         )
         
         # Get the stdio streams
         self.sequential_thinking_stdio, self.sequential_thinking_write = sequential_thinking_transport
         
         logger.info("Creating sequential-thinking MCP client session...")
         self.sequential_thinking_session = await self.exit_stack.enter_async_context(
            ClientSession(self.sequential_thinking_stdio, self.sequential_thinking_write)
         )
         
         # Initialize the session
         logger.info("Initializing sequential-thinking MCP session...")
         await self.sequential_thinking_session.initialize()
         
         logger.info("Successfully connected to sequential-thinking MCP server")
         return True
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP sequential-thinking server: {e}")
         return False
         
   async def close(self):
      """Close all MCP server connections and cleanup resources."""
      # Clean up the MCP client sessions
      if self.exit_stack:
         try:
            await self.exit_stack.aclose()
         except Exception as e:
            logger.warning(f"Error while closing exit stack: {e}")
         self.exit_stack = None
      
      # Clear all references
      self.filesystem_session = None
      self.memory_session = None
      self.sequential_thinking_session = None
      self.tools = []
      self.filesystem_stdio = None
      self.filesystem_write = None
      self.memory_stdio = None
      self.memory_write = None
      self.sequential_thinking_stdio = None
      self.sequential_thinking_write = None
      
   async def disconnect(self):
      """Alias for close() for backward compatibility."""
      await self.close()

   def get_openai_tools(self) -> List[Dict[str, Any]]:
      """Convert MCP tools to OpenAI-compatible format."""
      openai_tools = []
      
      for tool in self.tools:
         # Skip tools with missing required fields
         if not hasattr(tool, 'name') or not tool.name:
            logger.warning(f"Skipping tool with missing name: {tool}")
            continue
            
         if not hasattr(tool, 'description'):
            logger.warning(f"Tool {tool.name} missing description, using default")
            description = f"Tool: {tool.name}"
         else:
            description = tool.description
            
         # Convert MCP tool format to OpenAI function format
         openai_tool = {
            "type": "function",
            "name": tool.name,
            "function": {
               "name": tool.name,
               "description": description,
               "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {
                  "type": "object",
                  "properties": {},
                  "required": []
               }
            }
         }
         openai_tools.append(openai_tool)
         
      return openai_tools
      
   async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
      """Execute a tool on the appropriate MCP server."""
      session = None
      
      # Determine which session to use based on available tools
      if self.filesystem_session:
         try:
            filesystem_tools = await self.filesystem_session.list_tools()
            if any(tool.name == tool_name for tool in filesystem_tools.tools):
               session = self.filesystem_session
         except Exception as e:
            logger.warning(f"Failed to check filesystem tools: {e}")
      
      if not session and self.memory_session:
         try:
            memory_tools = await self.memory_session.list_tools()
            if any(tool.name == tool_name for tool in memory_tools.tools):
               session = self.memory_session
         except Exception as e:
            logger.warning(f"Failed to check memory tools: {e}")
      
      if not session and self.sequential_thinking_session:
         try:
            sequential_thinking_tools = await self.sequential_thinking_session.list_tools()
            if any(tool.name == tool_name for tool in sequential_thinking_tools.tools):
               session = self.sequential_thinking_session
         except Exception as e:
            logger.warning(f"Failed to check sequential thinking tools: {e}")
      
      if not session:
         raise RuntimeError(f"No MCP server found for tool '{tool_name}'")
         
      try:
         # Call the tool on the appropriate MCP server
         result = await session.call_tool(tool_name, arguments)
         
         # Extract the content from the result
         if hasattr(result, 'content') and result.content:
            # MCP returns content as a list of content items
            if isinstance(result.content, list) and len(result.content) > 0:
               content_item = result.content[0]
               if hasattr(content_item, 'text'):
                  return {"result": content_item.text}
               elif hasattr(content_item, 'data'):
                  return {"result": content_item.data}
            
         return {"result": str(result)}
         
      except Exception as e:
         logger.error(f"Error calling MCP tool {tool_name}: {e}")
         return {"error": str(e)}
   
   @property
   def session(self):
      """Backward compatibility property - returns filesystem session if available."""
      return self.filesystem_session

# Global instance
mcp_client = MCPClient()