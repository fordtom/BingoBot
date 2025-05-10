"""Query command to interact with AI."""
import discord
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def execute(interaction: discord.Interaction, question: str):
    """Execute the query command.

    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
    """
    # Log the query for debugging
    logger.info(f"AI query from {interaction.user}: {question}")

    await interaction.response.defer()

    try:
        # Create a completion request with GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": question}
            ],
        )

        # Extract and send the response
        ai_response = response.choices[0].message.content
        formatted_response = f"Question:\n\n{question}\n\nAnswer:\n\n{ai_response}"
        await interaction.followup.send(formatted_response)

        # Log the response
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")