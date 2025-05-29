"""Utility functions for AI processing."""
import discord
import logging
import re
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def check_mcp_server(url: str, name: str) -> bool:
   """Check if an MCP server is responding.
   
   Args:
       url: The server URL to check
       name: The server name for logging
       
   Returns:
       bool: True if server is responding, False otherwise
   """
   try:
       # Try basic connectivity test
       response = requests.get(url, timeout=2)
       logger.debug(f"{name} server at {url} responded with status {response.status_code}")
       return True
   except requests.exceptions.RequestException as e:
       logger.warning(f"{name} server at {url} is not responding: {e}")
       return False

def get_mcp_tools() -> List[Dict]:
   """Get the configured MCP tools for OpenAI integration.
   
   Only includes tools for servers that are actually responding.
   
   Returns:
       List[Dict]: List of MCP tool configurations for available servers
   """
   all_tools = [
       {
           "type": "mcp",
           "server_url": "http://localhost:3001",
           "server_label": "memory",
           "allowed_tools": [
               "search_nodes", "create_entities", "create_relations", 
               "add_observations", "read_graph", "open_nodes", 
               "delete_entities", "delete_observations", "delete_relations"
           ]
       },
       {
           "type": "mcp", 
           "server_url": "http://localhost:3002",
           "server_label": "filesystem",
           "allowed_tools": [
               "read_file", "write_file", "edit_file", "create_directory", 
               "list_directory", "directory_tree", "move_file", "search_files", 
               "get_file_info", "list_allowed_directories", "read_multiple_files"
           ]
       },
       {
           "type": "mcp",
           "server_url": "http://localhost:3003",
           "server_label": "thinking", 
           "allowed_tools": ["sequentialthinking"]
       }
   ]
   
   # Filter to only include responding servers
   available_tools = []
   for tool in all_tools:
       if check_mcp_server(tool["server_url"], tool["server_label"]):
           available_tools.append(tool)
           logger.info(f"MCP server '{tool['server_label']}' is available")
       else:
           logger.warning(f"MCP server '{tool['server_label']}' is not available, skipping")
   
   return available_tools

async def resolve_mentions(interaction: discord.Interaction, text: str) -> str:
   """Convert Discord mentions to usernames.
   
   Args:
       interaction: The Discord interaction object
       text: Text containing Discord mentions
       
   Returns:
       str: Text with mentions converted to usernames
   """
   mention_pattern = r'<@!?(\d+)>'
   mentions = re.finditer(mention_pattern, text)
   replacements = {}
   
   for match in mentions:
       user_id = match.group(1)
       guild = interaction.guild
       if guild:
           try:
               # Try cached member lookup first
               mentioned_member = guild.get_member(int(user_id))
               
               # If not cached, fetch from Discord API
               if not mentioned_member:
                   try:
                       mentioned_member = await guild.fetch_member(int(user_id))
                   except (discord.NotFound, discord.HTTPException) as e:
                       logger.warning(f"Could not fetch member {user_id}: {e}")
                       continue
               
               if mentioned_member:
                   logger.debug(f"Resolving mention {match.group(0)} to {mentioned_member.name}")
                   replacements[match.group(0)] = mentioned_member.name
           except (ValueError, Exception) as e:
               logger.warning(f"Error resolving mention {user_id}: {e}")
   
   # Apply replacements
   for mention, username in replacements.items():
       text = text.replace(mention, username)
   
   return text

async def restore_mentions(interaction: discord.Interaction, response: str) -> str:
   """Convert usernames back to Discord mentions in AI response.
   
   Args:
       interaction: The Discord interaction object
       response: The AI response string
       
   Returns:
       str: Response with usernames converted back to mentions
   """
   guild = interaction.guild
   if not guild:
       return response
   
   try:
       # Get guild members
       members = guild.members
       if len(members) < 10:  # Fetch if we don't have many cached
           members = [member async for member in guild.fetch_members(limit=None)]
   except Exception as e:
       logger.warning(f"Could not fetch guild members: {e}")
       return response
   
   # Create username to member mapping
   username_to_member = {member.name.lower(): member for member in members}
   
   # Include display names
   for member in members:
       if member.display_name != member.name:
           username_to_member[member.display_name.lower()] = member
   
   modified_response = response
   
   # Handle @username patterns
   at_pattern = r'@([a-zA-Z0-9_]+)'
   def replace_at_mention(match):
       username = match.group(1).lower()
       if username in username_to_member:
           member = username_to_member[username]
           logger.debug(f"Converting @{username} to mention")
           return member.mention
       return match.group(0)
   
   modified_response = re.sub(at_pattern, replace_at_mention, modified_response)
   
   # Handle standalone usernames (longest first to avoid partial matches)
   sorted_usernames = sorted(username_to_member.keys(), key=len, reverse=True)
   
   for username in sorted_usernames:
       member = username_to_member[username]
       pattern = r'\b' + re.escape(username) + r'\b'
       
       def replace_username(match):
           logger.debug(f"Converting standalone username '{match.group(0)}' to mention")
           return member.mention
       
       modified_response = re.sub(pattern, replace_username, modified_response, flags=re.IGNORECASE)
   
   return modified_response

def extract_ai_response(response) -> str:
   """Extract the final AI response from OpenAI response object.
   
   Args:
       response: OpenAI response object
       
   Returns:
       str: The extracted AI response text
   """
   if not response.output or len(response.output) == 0:
       return "I apologize, but I couldn't generate a response."
   
   logger.debug(f"Response output length: {len(response.output)}")
   logger.debug(f"Response output items: {[type(item).__name__ for item in response.output]}")
   
   # Find the final assistant message
   for i, item in enumerate(reversed(response.output)):
       logger.debug(f"Item {i}: type={type(item).__name__}, has role={hasattr(item, 'role')}")
       
       if hasattr(item, 'role') and item.role == 'assistant':
           logger.debug(f"Found assistant message: has content={hasattr(item, 'content')}")
           
           if hasattr(item, 'content') and item.content:
               logger.debug(f"Content type: {type(item.content)}")
               
               if isinstance(item.content, list) and len(item.content) > 0:
                   if hasattr(item.content[0], 'text'):
                       return item.content[0].text
                   else:
                       return str(item.content[0])
               elif isinstance(item.content, str):
                   return item.content
               break
   
   return "I apologize, but I couldn't generate a response."