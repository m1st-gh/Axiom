from datetime import datetime
import os
import sys
import logging


import discord
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from typing import Any
from apis.orclient import OpenRouterClient


# --- Environment Variable Helper ---
def require_env_vars(*names: str) -> dict[str, Any]:
    """Loads required environment variables from .env or environment.
    If a variable contains commas, it is parsed as a list of strings.
    """
    load_dotenv()
    env_values: dict[str, Any] = {}
    missing_vars: list[str] = []

    for name in names:
        value = os.getenv(name)
        if value is None:
            missing_vars.append(name)
        else:
            # If the value contains a comma, parse as list
            if "," in value:
                env_values[name] = [item.strip() for item in value.split(",")]
            else:
                env_values[name] = value

    if missing_vars:
        error_message = (
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        print(f"CRITICAL: {error_message}", file=sys.stderr)
        sys.exit(1)
    return env_values


def setup_logging():
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    return logging.getLogger("discord")


logger = setup_logging()

# --- Main Execution ---
env = require_env_vars("DISCORD_TOKEN", "DISCORD_GUILD_ID", "OPENROUTER_API_KEY")

# Parse guild IDs as a list of ints
try:
    if isinstance(env["DISCORD_GUILD_ID"], list):
        guild_ids = [int(gid) for gid in env["DISCORD_GUILD_ID"]]
    else:
        guild_ids = [int(env["DISCORD_GUILD_ID"])]
except ValueError:
    logger.critical("DISCORD_GUILD_ID must be integer(s).")
    print("CRITICAL: DISCORD_GUILD_ID must be integer(s).", file=sys.stderr)
    sys.exit(1)

bot = commands.Bot(
    command_prefix=commands.when_mentioned, intents=discord.Intents.default()
)

# Setup database
db = TinyDB("axiom_db.json")
pin_channels = db.table("pin_channels")
jarvis_messages = db.table("jarvis_messages")

# Setup Openrouter

jarvis = OpenRouterClient(api_key=env["OPENROUTER_API_KEY"])


# Set pin channel function
def set_pin_channel(guild_id: int, channel_id: int) -> None:
    """Set the pin channel for a guild."""
    Guild = Query()
    pin_channels.upsert(
        {"guild_id": guild_id, "channel_id": channel_id}, Guild.guild_id == guild_id
    )


@bot.event
async def on_ready() -> None:
    logger.info(
        f"Logged in as {bot.user} (ID: {bot.user.id})"  # pyright: ignore[reportOptionalMemberAccess]
    )
    logger.info(
        f"Bot active in {len(bot.guilds)} guild(s): "
        f"{', '.join(g.name for g in bot.guilds)}"
    )

    # Sync commands with the specified guilds
    try:
        for gid in guild_ids:
            guild = discord.Object(id=gid)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} command(s) to guild ID: {gid}")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")


@bot.tree.command(
    name="set_pin_channel", description="Set the current channel as the pin channel"
)
async def set_pin_channel_cmd(interaction: discord.Interaction):
    # Get the channel from the interaction
    guild_id = interaction.guild_id

    if (
        isinstance(channel := interaction.channel, discord.TextChannel)
        and isinstance(guild_id, int)
        and isinstance(channel.id, int)
    ):
        # Store the channel ID in the database
        set_pin_channel(guild_id, channel.id)
        message = f"Pin channel has been set to {channel.mention}"
    else:
        message = "Please use this command from the context of a guild text channel."

    # Confirm to the user
    await interaction.response.send_message(message)


@bot.tree.context_menu(name="Reprint message")
async def reprint(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(f"{message.content}")


async def get_channel_from_id(bot, channel_id: int) -> discord.TextChannel | None:
    """Get a channel object from its ID."""

    channel = bot.get_channel(channel_id)

    # If the channel isn't found in cache, fetch it
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            return None
    return channel if isinstance(channel, discord.TextChannel) else None


@bot.tree.context_menu(name="Pin message")
async def pin_message(interaction: discord.Interaction, message: discord.Message):
    Pin_channels = Query()
    # Use the interaction's guild_id to lookup the pin channel
    guild_id = interaction.guild_id
    result = pin_channels.search(Pin_channels.guild_id == guild_id)
    if not result:
        await interaction.response.send_message("Please use `/set_pin_channel` first")
        return
    channel = await get_channel_from_id(bot, result[0]["pin_channel_id"])
    if channel is None:
        await interaction.response.send_message("Pin channel not found.")
        return
    await interaction.response.send_message(channel.mention)
    await message.forward(channel)


@bot.tree.command(name="jarvis")
@discord.app_commands.describe(query="The message")
async def invoke_jarvis(interaction: discord.Interaction, query: str):
    message_history = jarvis_messages.all()
    to_remove: list[int] = []
    for message in message_history:
        timestamp = message["timestamp"]
        current_time = datetime.now().timestamp()
        if timestamp < current_time - 3600:
            to_remove.append(message.doc_id)
    if len(to_remove) != 0:
        jarvis_messages.remove(to_remove)
    message = {
        "role": "user",
        "content": query,
        "timestamp": datetime.now().timestamp(),
    }
    jarvis_messages.insert(message)
    message_history = jarvis_messages.all()
    return_message = jarvis.get_completion(
        model="meta-llama/llama-3.3-8b-instruct:free", messages=message_history
    )
    interaction.response.send_message(f"{return_message}")


bot.run(token=env["DISCORD_TOKEN"])
