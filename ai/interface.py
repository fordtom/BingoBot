import discord
import logging
import asyncio
from collections import deque
from ai.prompts import DISCORD_BOT_SYSTEM_PROMPT
from utils.discord_utils import resolve_mentions, restore_mentions
from ai.utils import create_mcp_servers

logger = logging.getLogger(__name__)

# Shared interaction history across all commands
interaction_history = deque(maxlen=10)
interaction_history_lock = asyncio.Lock()

# MCP servers are initialized once and shared across requests
_mcp_servers: list | None = None
_mcp_servers_lock = asyncio.Lock()

async def prepare_user_query(interaction: discord.Interaction, question: str) -> tuple[str, str]:
    """Build the final question with history and mention resolution."""
    question_with_usernames = await resolve_mentions(interaction, question)
    asking_username = interaction.user.name
    base_question = f"Asked by: {asking_username}\n\n{question_with_usernames}"

    history_lines = []
    for idx, (q, a) in enumerate(reversed(interaction_history), start=1):
        history_lines.append(f"previous interaction {idx}:")
        history_lines.append(f"Q: {q}")
        history_lines.append(f"A: {a}")
        history_lines.append("")

    history_text = "\n".join(history_lines)
    if history_text:
        enhanced_question = f"{history_text}\n{base_question}"
    else:
        enhanced_question = base_question

    return enhanced_question, base_question


async def get_mcp_servers():
    """Initialize and return the shared MCP servers."""
    global _mcp_servers
    if _mcp_servers is None:
        async with _mcp_servers_lock:
            if _mcp_servers is None:
                try:
                    _mcp_servers = create_mcp_servers()
                    for server in _mcp_servers:
                        await server.connect()
                    logger.info(f"Initialized {_mcp_servers!r}")
                except Exception as e:
                    logger.error(f"Failed to initialize MCP servers: {e}")
                    _mcp_servers = []
    return _mcp_servers

async def run_agent_async(enhanced_question: str) -> str:
    """Run the OpenAI agent with the given question."""
    try:
        from agents import Agent, Runner
    except ImportError as e:
        logger.error(f"Failed to import agents: {e}")
        return "Sorry, the AI agent system is not available."

    try:
        mcp_servers = await get_mcp_servers()
        agent = Agent(
            name="discord-assistant",
            instructions=DISCORD_BOT_SYSTEM_PROMPT,
            model="gpt-4.1-mini",
            mcp_servers=mcp_servers,
        )
        logger.info(f"Running agent with {len(mcp_servers)} MCP servers")
        result = await Runner.run(agent, enhanced_question)
        if hasattr(result, "final_output"):
            return result.final_output
        return str(result)
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

async def ask_question(
    interaction: discord.Interaction,
    question: str,
    prepend_instruction: str | None = None,
) -> str:
    """Send a question to the agent and return the response."""
    if prepend_instruction:
        question = f"{prepend_instruction}\n\n{question}"

    enhanced_question, base_question = await prepare_user_query(interaction, question)
    ai_response = await run_agent_async(enhanced_question)
    async with interaction_history_lock:
        interaction_history.append((base_question, ai_response))
    ai_response_with_mentions = await restore_mentions(interaction, ai_response)
    return ai_response_with_mentions
