"""Query command to interact with AI using the agents package."""
import discord
import logging

from ai.prompts import DISCORD_BOT_SYSTEM_PROMPT
from ai.utils import resolve_mentions, restore_mentions

logger = logging.getLogger(__name__)

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

async def run_agent_async(enhanced_question: str, use_web_search: bool = True) -> str:
    """Run the Agent with proper async MCP server handling.
    
    Args:
        enhanced_question: The prepared question
        use_web_search: Whether to enable web search
        
    Returns:
        str: The AI response
    """
    try:
        from agents import Agent, Runner
        from agents.mcp.server import MCPServerStdio
    except ImportError as e:
        logger.error(f"Failed to import agents: {e}")
        return "Sorry, the AI agent system is not available."
    
    try:
        mcp_servers = []
        
        # Create MCP servers with async context managers
        async with MCPServerStdio(
            name="Memory Server",
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
                "env": {"MEMORY_FILE_PATH": "/data/memory.json"}
            },
            cache_tools_list=True
        ) as memory_server:
            mcp_servers.append(memory_server)
            logger.info("Added memory MCP server")
            
            async with MCPServerStdio(
                name="Filesystem Server", 
                params={
                    "command": "npx", 
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"]
                },
                cache_tools_list=True
            ) as filesystem_server:
                mcp_servers.append(filesystem_server)
                logger.info("Added filesystem MCP server")
                
                async with MCPServerStdio(
                    name="Thinking Server",
                    params={
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
                    },
                    cache_tools_list=True
                ) as thinking_server:
                    mcp_servers.append(thinking_server)
                    logger.info("Added thinking MCP server")
                    
                    # Create agent using the agents package
                    agent = Agent(
                        name="discord-assistant",
                        instructions=DISCORD_BOT_SYSTEM_PROMPT,
                        model="gpt-4.1-mini",
                        mcp_servers=mcp_servers
                    )
                    
                    # Run the agent
                    logger.info(f"Running agent with {len(mcp_servers)} MCP servers")
                    result = await Runner.run(agent, enhanced_question)
                    
                    # Extract the response text
                    if hasattr(result, 'final_output'):
                        return result.final_output
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
        # Run the agent with proper async MCP server handling
        logger.info("Starting Agent with MCP servers...")
        ai_response = await run_agent_async(enhanced_question, use_web_search)
        
        # Convert usernames back to mentions in the AI response
        ai_response_with_mentions = await restore_mentions(interaction, ai_response)
        
        # Format and send response
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response_with_mentions}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error in AI query execution: {e}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")