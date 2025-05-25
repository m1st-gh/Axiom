import discord
from discord.ext import commands
import asyncio
import sys
import logging
from core import logger
from core.config import config
from core.commands import load_commands


class DiscordBot:
    """Main Discord bot class."""

    def __init__(self):
        self.config = config.require_env_vars(
            "DISCORD_TOKEN",
            "DISCORD_GUILD_ID",
            "OPENROUTER_API_KEY",
            "DB_PATH",
            "AI_SYSTEM_PROMPT_PATH",
            "AI_SUMMARY_PROMPT_PATH",
        )

        self.guild_ids = config.get_guild_ids()

        intents = discord.Intents.default()
        intents.message_content = True

        self.bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)

        # Set up events
        self.bot.event(self.on_ready)

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info(
            f"Bot active in {len(self.bot.guilds)} guild(s): "
            f"{', '.join(g.name for g in self.bot.guilds)}"
        )

        # Sync commands with the specified guilds
        try:
            for gid in self.guild_ids:
                guild = discord.Object(id=gid)
                self.bot.tree.copy_global_to(guild=guild)
                synced = await self.bot.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} command(s) to guild ID: {gid}")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def setup(self):
        """Set up the bot by loading commands."""
        await load_commands(self.bot)

    def run(self):
        """Run the bot and ensure Discord.py uses our logger."""
        # --- Overwrite discord.py logger handlers with our own ---
        discord_logger = logger  # Use our global logger
        discordpy_logger = discord.utils.setup_logging  # discord.py's helper

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
        """Start the bot asynchronously."""
        await self.setup()
        await self.bot.start(self.config.get("DISCORD_TOKEN"))


if __name__ == "__main__":
    bot = DiscordBot()
    bot.run()
