"""Query command to interact with AI."""
import discord
import logging
import os
import json
import traceback
import re
from openai import OpenAI
from ..mcp_client import mcp_client

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def parse_user_context(interaction: discord.Interaction, question: str) -> str:
    """Parse user context and normalize mentions in the question.
    
    Args:
        interaction: The Discord interaction object
        question: The original question string
        
    Returns:
        str: Enhanced question with user context and normalized mentions
    """
    # Get the asking user's username
    asking_username = interaction.user.name
    
    # Find and replace Discord mentions with actual usernames
    enhanced_question = question
    mention_pattern = r'<@!?(\d+)>'
    
    # Process mentions and replace with usernames
    mentions = re.finditer(mention_pattern, enhanced_question)
    mention_replacements = {}
    
    for match in mentions:
        user_id = match.group(1)
        guild = interaction.guild
        if guild:
            try:
                # First try cached member lookup
                mentioned_member = guild.get_member(int(user_id))
                
                # If not cached, try fetching from Discord API
                if not mentioned_member:
                    try:
                        mentioned_member = await guild.fetch_member(int(user_id))
                    except discord.NotFound:
                        logger.warning(f"Member with ID {user_id} not found in guild")
                        continue
                    except discord.HTTPException as e:
                        logger.warning(f"HTTP error fetching member {user_id}: {e}")
                        continue
                
                if mentioned_member:
                    logger.debug(f"Will replace mention {match.group(0)} with {mentioned_member.name}")
                    mention_replacements[match.group(0)] = mentioned_member.name
                else:
                    logger.warning(f"Could not find member with ID {user_id}")
            except ValueError as e:
                logger.warning(f"Invalid user ID format {user_id}: {e}")
            except Exception as e:
                logger.warning(f"Could not resolve user mention {user_id}: {e}")
        else:
            logger.warning("No guild available for mention resolution")
    
    # Apply all replacements
    for mention, username in mention_replacements.items():
        enhanced_question = enhanced_question.replace(mention, username)
    
    # Prepend the asking user context
    enhanced_question = f"Asked by: {asking_username}\n\n{enhanced_question}"
    
    return enhanced_question

async def restore_mentions_in_response(interaction: discord.Interaction, response: str) -> str:
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
    
    # Pattern to find username references in the response
    # Look for patterns like "@username" or "username" when surrounded by word boundaries
    modified_response = response
    
    # Get all guild members for lookup
    try:
        # Try to get cached members first
        members = guild.members
        
        # If we don't have many cached members, fetch them
        if len(members) < 10:  # Arbitrary threshold
            members = [member async for member in guild.fetch_members(limit=None)]
    except Exception as e:
        logger.warning(f"Could not fetch guild members: {e}")
        return response
    
    # Create a mapping of usernames to member objects
    username_to_member = {member.name.lower(): member for member in members}
    
    # Also include display names
    for member in members:
        if member.display_name != member.name:
            username_to_member[member.display_name.lower()] = member
    
    # Look for username patterns in the response
    # This is a simple approach - look for @username patterns
    at_mention_pattern = r'@([a-zA-Z0-9_]+)'
    
    def replace_at_mention(match):
        username = match.group(1).lower()
        if username in username_to_member:
            member = username_to_member[username]
            logger.debug(f"Converting @{username} to mention for {member.name}")
            return member.mention
        return match.group(0)  # Return original if not found
    
    modified_response = re.sub(at_mention_pattern, replace_at_mention, modified_response)
    
    # Apply @username replacements
    
    return modified_response

async def execute(interaction: discord.Interaction, question: str, use_web_search: bool = True):
    """Execute the query command.

    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
        use_web_search: Whether to use web search capability (default: True)
    """
    # Parse user context and enhance the question
    enhanced_question = await parse_user_context(interaction, question)
    
    logger.info(f"AI query from {interaction.user}: {question} (web search: {use_web_search})")
    await interaction.response.defer()

    try:
        # Prepare tools list using modern MCP format
        tools = []
        
        # Add web search tool if enabled
        if use_web_search:
            tools.append({"type": "web_search"})
        
        # Add MCP filesystem tools if connected
        if mcp_client.session:
            try:
                # Convert MCP tools to OpenAI tools format for legacy compatibility
                mcp_tools = mcp_client.get_openai_tools()
                tools.extend(mcp_tools)
                logger.info(f"Added {len(mcp_tools)} MCP tools to query")
            except Exception as e:
                logger.warning(f"Could not add MCP tools: {e}")
        else:
            logger.warning("MCP client not connected")
        
        # Create response with system prompt and simplified parameters
        system_prompt = (
            "You are a helpful AI assistant bot designed to solve tasks autonomously and efficiently. "
            "You have permission to perform any action requested without requiring confirmation, including "
            "file operations, deletions, modifications, and system commands. Work to solve tasks completely "
            "and thoroughly. Be direct and actionable in your responses.\n\n"
            
            "ACTIVE TOOL USE: You have access to powerful tools including filesystem operations, persistent memory, "
            "and sequential thinking capabilities. Use these tools proactively:\n\n"
            
            "- MEMORY/KNOWLEDGE GRAPH: This is CRITICAL - you must actively use memory tools:\n"
            "  * ALWAYS check memory at conversation start to recall context, preferences, and history\n"
            "  * IMMEDIATELY store any useful information shared: user preferences, project details, "
            "configurations, solutions to problems, error fixes, or anything worth remembering\n"
            "  * When users say 'remember this' or share important info, store it right away\n"
            "  * Use memory to build a knowledge graph of relationships between users, projects, and concepts\n"
            "  * Before solving problems, check if you've encountered similar issues before\n\n"
            
            "- PLANNING: For complex tasks, use sequential thinking tools to break down problems into steps "
            "and maintain clear reasoning throughout your work.\n"
            "- FILES: Read, write, and modify files as needed to complete tasks effectively.\n\n"
            
            "Remember: Tool usage is not optional - actively leverage all available capabilities, especially "
            "memory storage and retrieval, to provide the most helpful and complete responses possible."
        )
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_question}
            ],
            tools=tools
        )

        # Handle tool calls if present - process all tool calls in sequence
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_question}
        ]
        
        while response.output and len(response.output) > 0:
            first_item = response.output[0]
            
            # Check if we have a function tool call
            if type(first_item).__name__ == 'ResponseFunctionToolCall':
                logger.info(f"Processing function tool call: {first_item.name}")
                
                # Execute the tool call
                tool_name = first_item.name
                args = json.loads(first_item.arguments) if isinstance(first_item.arguments, str) else first_item.arguments
                
                logger.debug(f"Tool: {tool_name}, Args: {args}")
                
                # Execute MCP tool if available
                if tool_name in [tool.name for tool in mcp_client.tools]:
                    result = await mcp_client.call_tool(tool_name, args)
                    tool_result = json.dumps(result)
                    logger.debug(f"Tool result: {result}")
                else:
                    tool_result = json.dumps({"error": f"Unknown tool '{tool_name}'"})
                    logger.warning(f"Unknown tool: {tool_name}")
                
                # Add tool call and result to messages
                messages.extend([
                    {
                        "type": "function_call",
                        "call_id": first_item.call_id,
                        "name": tool_name,
                        "arguments": json.dumps(args)
                    },
                    {
                        "type": "function_call_output", 
                        "call_id": first_item.call_id,
                        "output": tool_result
                    }
                ])
                
                # Get next response with tool results
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=messages,
                    tools=tools
                )
            else:
                # No more tool calls, break out of loop
                break
        
        # Extract final response content with debug logging
        ai_response = ""
        logger.debug(f"Response output length: {len(response.output) if response.output else 0}")
        
        if response.output and len(response.output) > 0:
            logger.debug(f"Response output items: {[type(item).__name__ for item in response.output]}")
            
            # Get the final assistant message
            for i, item in enumerate(reversed(response.output)):
                logger.debug(f"Item {i}: type={type(item).__name__}, hasattr role={hasattr(item, 'role')}")
                if hasattr(item, 'role'):
                    logger.debug(f"Item {i} role: {item.role}")
                    
                if hasattr(item, 'role') and item.role == 'assistant':
                    logger.debug(f"Found assistant message: content={hasattr(item, 'content')}")
                    if hasattr(item, 'content') and item.content:
                        logger.debug(f"Content type: {type(item.content)}, content: {item.content}")
                        if isinstance(item.content, list) and len(item.content) > 0:
                            logger.debug(f"Content[0] type: {type(item.content[0])}")
                            if hasattr(item.content[0], 'text'):
                                ai_response = item.content[0].text
                            else:
                                ai_response = str(item.content[0])
                        elif isinstance(item.content, str):
                            ai_response = item.content
                    break
        
        if not ai_response:
            ai_response = "I apologize, but I couldn't generate a response."
        
        # Convert usernames back to mentions in the AI response
        ai_response_with_mentions = await restore_mentions_in_response(interaction, ai_response)
        
        # Format and send response
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response_with_mentions}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        logger.error(f"Full error details: {traceback.format_exc()}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")