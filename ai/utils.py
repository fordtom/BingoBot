"""Utility functions for AI processing."""
import discord
import logging
import re

logger = logging.getLogger(__name__)

def create_mcp_servers():
   """Create the configured MCP servers for the agents package.
   
   Returns:
       List: List of MCPServerStdio instances for the agents package
   """
   try:
       from agents.mcp.server import MCPServerStdio
   except ImportError as e:
       logger.error(f"Failed to import agents.MCPServerStdio: {e}")
       return []
   
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