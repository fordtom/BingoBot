"""Simple voltage monitoring cog for Discord bot.

Sends a simple message to #general when undervoltage file exists.
"""
import logging
import os

import discord
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)

UNDERVOLTAGE_FILE = "/db/undervoltage"


class MonitoringCog(commands.Cog):
    """Simple cog for voltage monitoring."""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_voltage_status.start()
        
    async def cog_load(self):
        """Initialize the cog."""
        logger.info("Monitoring cog loaded")
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded."""
        self.check_voltage_status.cancel()
        logger.info("Monitoring cog unloaded")
            
    async def _send_voltage_notification(self):
        """Send simple voltage warning to #general."""
        # Find #general channel
        channel = None
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="general")
            if channel:
                break
                
        if not channel:
            logger.error("Could not find #general channel")
            return
            
        try:
            await channel.send("i am undervolting :(")
            logger.info("Sent voltage warning to #general")
        except discord.HTTPException as e:
            logger.error(f"Failed to send voltage notification: {e}")
    
    @tasks.loop(minutes=5)
    async def check_voltage_status(self):
        """Check for voltage warnings and send notification."""
        try:
            # If the undervoltage file exists, send warning
            if os.path.exists(UNDERVOLTAGE_FILE):
                await self._send_voltage_notification()
                
        except Exception as e:
            logger.error(f"Error checking voltage status: {e}")
    
    @check_voltage_status.before_loop
    async def before_check_voltage_status(self):
        """Wait for bot to be ready before starting the task."""
        await self.bot.wait_until_ready()

async def setup(bot):
    """Set up the monitoring cog."""
    await bot.add_cog(MonitoringCog(bot)) 