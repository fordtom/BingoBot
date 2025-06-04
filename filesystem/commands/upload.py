"""Command to upload a file to the server."""
import os
import logging
import discord

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/data/uploads"


async def execute(interaction: discord.Interaction, file: discord.Attachment):
    """Save the uploaded file to the uploads directory."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_bytes = await file.read()
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        await interaction.response.send_message(
            f"Uploaded `{file.filename}` successfully.")
        logger.info(
            f"File {file.filename} uploaded by {interaction.user} to {save_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        await interaction.response.send_message(
            "Failed to save the uploaded file.")
