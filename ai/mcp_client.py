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
         
         # Create server parameters
         server_params = StdioServerParameters(
            command="npx",
            args=["@modelcontextprotocol/server-filesystem", "/nas"]
         )
         
         # Create stdio transport
         stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
         )
         
         # Set up session
         self.stdio, self.write = stdio_transport
         self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
         )
         
         # Initialize the session
         await self.session.initialize()
         
         # Get available tools from the server
         tools_response = await self.session.list_tools()
         self.tools = tools_response.tools
         
         logger.info(f"Connected to MCP filesystem server with {len(self.tools)} tools")
         return True
         
      except Exception as e:
         logger.error(f"Failed to connect to MCP filesystem server: {e}")
         return False
         
   async def disconnect(self):
      """Disconnect from the MCP server."""
      if self.exit_stack:
         await self.exit_stack.aclose()
         self.exit_stack = None
         self.session = None
         self.stdio = None
         self.write = None
         
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