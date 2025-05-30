"""Query command to interact with AI using the agents package."""
import discord
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ai.prompts import DISCORD_BOT_SYSTEM_PROMPT
from ai.utils import create_mcp_servers, resolve_mentions, restore_mentions

logger = logging.getLogger(__name__)

# Thread pool for running synchronous Agent operations
executor = ThreadPoolExecutor(max_workers=2)

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

def run_agent_sync(enhanced_question: str, use_web_search: bool = True) -> str:
    """Run the Agent synchronously (for use in thread pool).
    
    Args:
        enhanced_question: The prepared question
        use_web_search: Whether to enable web search
        
    Returns:
        str: The AI response
    """
    try:
        from agents import Agent, Runner
    except ImportError as e:
        logger.error(f"Failed to import agents: {e}")
        return "Sorry, the AI agent system is not available."
    
    try:
        # Create a new event loop for this thread
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create MCP servers
        mcp_servers = create_mcp_servers()
        
        # Create agent using the agents package
        agent = Agent(
            name="discord-assistant",
            instructions=DISCORD_BOT_SYSTEM_PROMPT,
            model="gpt-4.1-mini",
            mcp_servers=mcp_servers
        )
        
        # Run the agent
        logger.info(f"Running agent with {len(mcp_servers)} MCP servers")
        result = Runner.run_sync(agent, enhanced_question)
        
        # Extract the response text
        if hasattr(result, 'final_output'):
            return result.final_output
        elif hasattr(result, 'text'):
            return result.text
        elif hasattr(result, 'content'):
            return result.content
        else:
            return str(result)
            
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

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
        # Run the agent in a thread pool since it's synchronous
        logger.info("Starting Agent with MCP servers...")
        loop = asyncio.get_event_loop()
        ai_response = await loop.run_in_executor(
            executor, 
            run_agent_sync, 
            enhanced_question, 
            use_web_search
        )
        
        # Convert usernames back to mentions in the AI response
        ai_response_with_mentions = await restore_mentions(interaction, ai_response)
        
        # Format and send response
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response_with_mentions}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error in AI query execution: {e}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")