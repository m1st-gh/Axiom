import discord
from discord.ext import commands
import logging
import asyncio
from axiom import logger
from dotenv import load_dotenv
import sys
from pathlib import Path
from typing import Optional
from axiom.database import db
from axiom.config import Config


class Axiom:
    """Main Discord bot class."""

    def __init__(self, config_path: Optional[Path] = None):
        try:
            self.config = Config(config_path)
            self.discord_api_token = self.config.discord_api_token
            self.guild_ids = self.config.guild_ids
        except FileNotFoundError:
            logger.error(f"Configuration file not found at {config_path}")
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
        db.ensure_schema()
        logger.info(f"Logged in as {self.bot.user}")
        try:
            if self.guild_ids:
                for gid in self.guild_ids:
                    guild = discord.Object(id=gid)
                    self.bot.tree.copy_global_to(guild=guild)
                    synced = await self.bot.tree.sync(guild=guild)
                    guild_obj = self.bot.get_guild(gid)
                    guild_name = guild_obj.name if guild_obj else "Unknown Guild"
                    logger.info(
                        f"Synced {len(synced)} command(s) to guild ID: {gid} ({guild_name})"
                    )
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def setup(self):
        """Load all commands from the commands folder."""
        commands_dir = Path(__file__).parent / "commands"
        for extension in commands_dir.glob("*.py"):
            if extension.name != "__init__.py" and extension.is_file():
                try:
                    await self.bot.load_extension(f"axiom.commands.{extension.stem}")
                    logger.info(f"Loaded extension: {extension.stem}")
                except Exception as e:
                    logger.error(f"Failed to load extension {extension.stem}: {e}")

    def run(self):
        """Run the bot and ensure Discord.py uses our logger."""
        # --- Overwrite discord.py logger handlers with our own ---

        # Remove all handlers from discord.py's logger and add ours
        discord_logger_obj = logging.getLogger("discord")
        discord_logger_obj.handlers.clear()
        for handler in logger.handlers:
            discord_logger_obj.addHandler(handler)
        discord_logger_obj.setLevel(logging.WARNING)  # Or INFO/DEBUG as needed

        # Now run the bot
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Bot shutdown initiated by user")
            sys.exit(0)

    async def start(self):
        await self.setup()
        await self.bot.start(self.discord_api_token)
