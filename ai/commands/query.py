"""Query command to interact with AI."""
import discord
import logging
import os
from openai import OpenAI

from ai.prompts import DISCORD_BOT_SYSTEM_PROMPT
from ai.utils import get_mcp_tools, resolve_mentions, restore_mentions, extract_ai_response

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def prepare_user_query(interaction: discord.Interaction, question: str) -> str:
    """Prepare user query with context and resolved mentions.
    
    Args:
        interaction: The Discord interaction object
        question: The original question string
        
    Returns:
        str: Enhanced question with user context and normalized mentions
    """
    # Resolve Discord mentions to usernames
    question_with_usernames = await resolve_mentions(interaction, question)
    
    # Add user context
    asking_username = interaction.user.name
    enhanced_question = f"Asked by: {asking_username}\n\n{question_with_usernames}"
    
    return enhanced_question


async def execute(interaction: discord.Interaction, question: str, use_web_search: bool = True):
    """Execute the query command.

    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
        use_web_search: Whether to use web search capability (default: True)
    """
    # Prepare user query with context and resolved mentions
    enhanced_question = await prepare_user_query(interaction, question)
    
    logger.info(f"AI query from {interaction.user}: {question} (web search: {use_web_search})")
    await interaction.response.defer()

    try:
        # Prepare tools list
        tools = []
        
        # Add web search tool if enabled
        if use_web_search:
            tools.append({"type": "web_search"})
        
        # Add MCP tools
        try:
            tools.extend(get_mcp_tools())
            logger.info("Added native MCP server integrations")
        except Exception as e:
            logger.warning(f"Could not configure MCP servers: {e}")
        
        # Create response with system prompt
        
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": DISCORD_BOT_SYSTEM_PROMPT},
                {"role": "user", "content": enhanced_question}
            ],
            tools=tools
        )

        # Extract AI response and restore mentions
        ai_response = extract_ai_response(response)
        ai_response_with_mentions = await restore_mentions(interaction, ai_response)
        
        # Format and send response
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response_with_mentions}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")