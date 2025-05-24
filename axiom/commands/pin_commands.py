import discord
from discord.ext import commands
from discord import app_commands

from axiom import logger
from axiom.database.handlers import set_pin_channel, get_pin_channel


class PinCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="set_pin_channel", description="Set the current channel as the pin channel"
    )
    async def set_pin_channel_cmd(self, interaction: discord.Interaction):
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command must be used in a server."
            )
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Please use this command in a text channel."
            )
            return

        set_pin_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"Pin channel has been set to {channel.mention}"
        )
        logger.info(f"Set pin channel to {channel.id} in guild {interaction.guild_id}")

    async def _get_channel_from_id(self, channel_id: int) -> discord.TextChannel | None:
        """Get a channel object from its ID."""
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except discord.NotFound:
                logger.warning(f"Channel {channel_id} not found")
                return None
        return channel if isinstance(channel, discord.TextChannel) else None


# --- Context Menu Commands (must be at module level) ---


@app_commands.context_menu(name="Reprint message")
async def reprint(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message(f"{message.content}")


@app_commands.context_menu(name="Pin message")
async def pin_message(interaction: discord.Interaction, message: discord.Message):
    if not interaction.guild_id:
        await interaction.response.send_message(
            "This command must be used in a server."
        )
        return

    pin_channel_data = get_pin_channel(interaction.guild_id)
    if not pin_channel_data:
        await interaction.response.send_message("Please use `/set_pin_channel` first")
        return

    # Get the cog to use its helper method
    cog = interaction.client.get_cog("PinCommands")
    if not cog:
        await interaction.response.send_message("PinCommands cog not loaded.")
        return

    channel = await cog._get_channel_from_id(pin_channel_data.channel_id)
    if not channel:
        await interaction.response.send_message(
            "Pin channel not found. It may have been deleted."
        )
        return

    await interaction.response.send_message(f"Pinned to {channel.mention}")
    # Forwarding is not a built-in discord.py method; you may want to send a copy instead:
    await channel.send(
        f"**Pinned message from {message.author.mention}:**\n{message.content}"
    )
    logger.info(f"Pinned message {message.id} to channel {channel.id}")


# --- Setup function ---


async def setup(bot: commands.Bot):
    await bot.add_cog(PinCommands(bot))
    bot.tree.add_command(reprint)
    bot.tree.add_command(pin_message)
