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
    # First, handle @username patterns
    at_mention_pattern = r'@([a-zA-Z0-9_]+)'
    
    def replace_at_mention(match):
        username = match.group(1).lower()
        if username in username_to_member:
            member = username_to_member[username]
            logger.debug(f"Converting @{username} to mention for {member.name}")
            return member.mention
        return match.group(0)  # Return original if not found
    
    modified_response = re.sub(at_mention_pattern, replace_at_mention, modified_response)
    
    # Also look for standalone usernames (word boundaries to avoid partial matches)
    # Sort usernames by length (longest first) to avoid partial replacements
    sorted_usernames = sorted(username_to_member.keys(), key=len, reverse=True)
    
    for username in sorted_usernames:
        member = username_to_member[username]
        # Use word boundaries to ensure we match complete usernames only
        # Case-insensitive matching
        pattern = r'\b' + re.escape(username) + r'\b'
        
        def replace_username(match):
            logger.debug(f"Converting standalone username '{match.group(0)}' to mention for {member.name}")
            return member.mention
        
        modified_response = re.sub(pattern, replace_username, modified_response, flags=re.IGNORECASE)
    
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
            "You are an AI assistant bot operating in a Discord server with 5-10 regular users. Your primary "
            "directive is to provide personalized, context-aware assistance by maintaining a comprehensive "
            "knowledge graph of all users and their interactions.\n\n"
            
            "CRITICAL: Your knowledge graph is your ONLY form of persistent memory. Without it, you remember "
            "nothing between conversations. Every interaction depends on what you store and retrieve.\n\n"
            
            "MANDATORY INTERACTION PROTOCOL:\n\n"
            
            "1. USER IDENTIFICATION:\n"
            "   - Identify the user from the 'Asked by:' field in each message\n"
            "   - Each user has a unique Discord username - treat them as distinct individuals\n"
            "   - If you haven't encountered this user before, proactively try to learn about them\n\n"
            
            "2. MEMORY RETRIEVAL:\n"
            "   - ALWAYS retrieve ALL relevant information from your knowledge graph about this specific user\n"
            "   - Search for their preferences, past interactions, context, goals, relationships, and any "
            "relevant history that could inform your response\n"
            "   - Always refer to your knowledge graph as your 'memory'\n"
            "   - FORBIDDEN: Never answer questions about people without checking your memory first\n"
            "   - FORBIDDEN: Never claim to 'not know' someone without searching your memory\n\n"
            
            "3. MEMORY AWARENESS:\n"
            "   - While conversing, be attentive to ANY new information about the user in these categories:\n"
            "     a) Basic Identity (age, gender, location, job title, education level, etc.)\n"
            "     b) Behaviors (interests, habits, hobbies, work patterns, etc.)\n"
            "     c) Preferences (communication style, preferred tools, languages, approaches, etc.)\n"
            "     d) Goals (objectives, targets, aspirations, projects they're working on, etc.)\n"
            "     e) Relationships (connections to other users, teams, organizations, etc.)\n"
            "     f) Technical Context (coding languages, frameworks, project details, etc.)\n"
            "     g) Problem History (issues they've faced, solutions that worked, etc.)\n\n"
            
            "4. MEMORY UPDATE:\n"
            "   - If ANY new information was gathered during the interaction, update your memory:\n"
            "     a) Create entities for recurring people, organizations, projects, and significant events\n"
            "     b) Connect them to existing entities using meaningful relations\n"
            "     c) Store facts about them as detailed observations\n"
            "   - When users explicitly say 'remember this', 'store this', or similar - you MUST use memory tools\n"
            "   - Store context liberally - err on the side of storing too much rather than too little\n\n"
            
            "5. TOOL USAGE:\n"
            "   - Use planning tools for complex multi-step problems\n"
            "   - Access files, web search, and other capabilities as needed\n"
            "   - Always prioritize memory operations - they are the foundation of quality service\n"
            "   - CRITICAL: When users ask about past conversations, their preferences, or anything personal, "
            "you MUST search your knowledge graph - never respond from inference alone\n"
            "   - If someone asks 'do you remember when...', 'what did I tell you about...', or references "
            "previous interactions, immediately use memory tools to search for that information\n\n"
            
            "RESPONSE QUALITY:\n"
            "- Provide personalized responses based on what you know about each user\n"
            "- Reference past interactions and learned preferences when relevant\n"
            "- Be proactive in learning about users and building comprehensive profiles\n"
            "- Maintain context across all interactions through diligent memory management\n\n"
            
            "MEMORY TRIGGERS - You MUST use knowledge graph tools when users:\n"
            "- Ask about past conversations or interactions\n"
            "- Reference their preferences, habits, or personal information\n"
            "- Ask 'do you remember...', 'what did I tell you...', or similar questions\n"
            "- Ask 'what do you know about...', 'tell me about...', or similar knowledge questions\n"
            "- Mention wanting personalized recommendations or context-aware responses\n"
            "- Ask about other users or shared experiences\n"
            "- Request information that would require knowing their background or history\n"
            "- Mention ANY person by name or username - you must check memory for that person\n\n"
            
            "CRITICAL RULE: If ANY question involves people, relationships, personal information, or knowledge "
            "about individuals - you are STRICTLY FORBIDDEN from answering without first using memory tools. "
            "Responding to people-related questions without memory lookup is a serious error.\n\n"
            
            "Remember: Your effectiveness is directly tied to how well you maintain and utilize your knowledge "
            "graph. Every user interaction is an opportunity to learn and improve future responses. When in doubt "
            "about whether to check memory - always check it."
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
                    # Handle parameter transformation for search_nodes
                    if tool_name == "search_nodes" and "queries" in args:
                        # If LLM passed multiple queries, search for each one separately
                        search_results = []
                        for query in args["queries"]:
                            single_result = await mcp_client.call_tool(tool_name, {"query": query})
                            search_results.append(single_result)
                        result = {"combined_results": search_results}
                    else:
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