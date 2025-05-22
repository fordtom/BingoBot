"""Query command to interact with AI."""
import discord
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def execute(interaction: discord.Interaction, question: str, use_web_search: bool = True):
    """Execute the query command.

    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
        use_web_search: Whether to use web search capability (default: True)
    """
    # Log the query for debugging
    logger.info(f"AI query from {interaction.user}: {question} (web search enabled)")

    await interaction.response.defer()

    try:
        # Prepare request parameters
        request_params = {
            "input": [{"role": "user", "content": question}],
            "model": "gpt-4.1-mini",
            "tools": [{"type": "web_search"}]  # Always enable web search
        }
        
        # Create a response request with GPT-4.1 Mini using the Responses API
        response = client.responses.create(**request_params)

        # Extract and send the response
        ai_response = response.output_text
        
        # Format response 
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response}"
        await interaction.followup.send(formatted_response)

        # Log the response
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")