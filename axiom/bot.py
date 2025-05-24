import discord
from discord.ext import commands
import asyncio
import sys

from axiom import logger
from axiom.config import config
from axiom.commands import load_commands


class AxiomBot:
    """Main Axiom Discord bot class."""

    def __init__(self):
        # Load required configuration
        self.config = config.require_env_vars(
            "DISCORD_TOKEN",
            "DISCORD_GUILD_ID",
            "OPENROUTER_API_KEY",
            "AXIOM_DB_PATH",
            "JARVIS_SYSTEM_PROMPT_PATH",
        )

        # Parse guild IDs
        self.guild_ids = config.get_guild_ids()

        # Initialize bot with intents
        intents = discord.Intents.default()

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
        """Run the bot."""
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
    bot = AxiomBot()
    bot.run()
