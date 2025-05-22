"""MCP client for connecting to the filesystem server."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import StdioServerParameters, create_stdio_client

logger = logging.getLogger(__name__)

class MCPFilesystemClient:
   """Client for interacting with the MCP filesystem server."""
   
   def __init__(self):
      self.client = None
      self.session = None
      self.tools = []
      
   async def connect(self):
      """Connect to the MCP filesystem server."""
      try:
         # Create client connection to the MCP server
         server_params = StdioServerParameters(
            command="npx",
            args=["@modelcontextprotocol/server-filesystem", "/nas"]
         )
         
         self.client = create_stdio_client("filesystem-server", "1.0")
         self.session = await self.client.connect(server_params)
         
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
      if self.session:
         await self.session.close()
         self.session = None
         self.client = None
         
   def get_openai_tools(self) -> List[Dict[str, Any]]:
      """Convert MCP tools to OpenAI-compatible format."""
      openai_tools = []
      
      for tool in self.tools:
         # Convert MCP tool format to OpenAI function format
         openai_tool = {
            "type": "function",
            "function": {
               "name": tool.name,
               "description": tool.description,
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