"""MCP client for connecting to the filesystem server."""
import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPFilesystemClient:
   """Client for interacting with the MCP filesystem server."""
   
   def __init__(self):
      self.session = None
      self.tools = []
      self.exit_stack = None
      self.stdio = None
      self.write = None
      
   async def connect(self):
      """Connect to the MCP filesystem server."""
      try:
         # Initialize exit stack
         self.exit_stack = AsyncExitStack()
         
         logger.info("Starting MCP filesystem server...")
         
         # Create server parameters for the filesystem server
         server_params = StdioServerParameters(
            command='npx',
            args=['-y', '@modelcontextprotocol/server-filesystem', '/nas', '/app/data'],
            env=None
         )
         
         logger.info("Creating stdio transport for MCP server...")
         
         # Create stdio transport using server parameters
         stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
         )
         
         # Get the stdio streams
         self.stdio, self.write = stdio_transport
         
         logger.info("Creating MCP client session...")
         self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
         )
         
         # Initialize the session
         logger.info("Initializing MCP session...")
         await self.session.initialize()
         
         # Get available tools from the server
         logger.info("Listing available tools...")
         tools_response = await self.session.list_tools()
         self.tools = tools_response.tools
         
         if not self.tools:
            logger.warning("No tools found in MCP server response")
            return False
            
         logger.info(f"Connected to MCP server. Available tools: {[t.name for t in self.tools]}")
         return True
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP filesystem server: {e}")
         return False
         
   async def close(self):
      """Close the MCP filesystem server connection and cleanup resources."""
      # Clean up the MCP client session
      if self.exit_stack:
         try:
            await self.exit_stack.aclose()
         except Exception as e:
            logger.warning(f"Error while closing exit stack: {e}")
         self.exit_stack = None
      
      # Clear all other references
      self.session = None
      self.tools = []
      self.stdio = None
      self.write = None
      
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
      """Execute a tool on the MCP server."""
      if not self.session:
         raise RuntimeError("Not connected to MCP server")
         
      try:
         # Call the tool on the MCP server
         result = await self.session.call_tool(tool_name, arguments)
         
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

# Global instance
mcp_client = MCPFilesystemClient()