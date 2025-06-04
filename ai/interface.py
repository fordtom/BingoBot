import discord
import logging
from collections import deque
from ai.prompts import DISCORD_BOT_SYSTEM_PROMPT
from ai.utils import resolve_mentions, restore_mentions

logger = logging.getLogger(__name__)

# Shared interaction history across all commands
interaction_history = deque(maxlen=10)

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

async def run_agent_async(enhanced_question: str) -> str:
    """Run the OpenAI agent with the given question."""
    try:
        from agents import Agent, Runner
        from agents.mcp.server import MCPServerStdio
    except ImportError as e:
        logger.error(f"Failed to import agents: {e}")
        return "Sorry, the AI agent system is not available."

    try:
        mcp_servers = []
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
    interaction_history.append((base_question, ai_response))
    ai_response_with_mentions = await restore_mentions(interaction, ai_response)
    return ai_response_with_mentions
