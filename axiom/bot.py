import discord
from discord.ext import commands
import asyncio
import sys
import logging
from pathlib import Path
from typing import Optional

from axiom.config import Config

logger = logging.getLogger(__name__)


class Axiom:
    """Main Discord bot class."""

    def __init__(self, config_path: Optional[Path] = None):
        try:
            self.config = Config(config_path)
            self.discord_api_token = self.config.discord_api_token
            self.guild_ids = self.config.guild_ids
            logger.info("Configuration loaded successfully.")
        except FileNotFoundError:
            logger.error(
                f"Configuration file not found. Please create a config.json file."
            )
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
        self.bot.event(self.on_ready)

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        # Sync commands with the specified guilds
        try:
            if self.guild_ids:
                for gid in self.guild_ids:
                    guild = discord.Object(id=gid)
                    self.bot.tree.copy_global_to(guild=guild)
                    synced = await self.bot.tree.sync(guild=guild)
                    logger.info(f"Synced {len(synced)} command(s) to guild ID: {gid}")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def setup(self):
        # await load_commands(self.bot)
        pass

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Bot shutdown initiated by user")
            sys.exit(0)

    async def start(self):
        await self.setup()
        await self.bot.start(self.discord_api_token)
