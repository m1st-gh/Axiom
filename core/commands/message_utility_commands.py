import discord
from discord.ext import commands
from discord import app_commands

from core import logger
from core.database.handlers import set_channel_mapping, get_channel_mapping


class MessageUtilityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="set_forward_channel",
        description="Set the current channel for forwarding pinned messages",
    )
    async def set_forward_channel_cmd(self, interaction: discord.Interaction):
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

        set_channel_mapping(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"Forward channel has been set to {channel.mention}"
        )
        logger.info(
            f"Set forward channel to {channel.id} in guild {interaction.guild_id}"
        )

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


@app_commands.context_menu(name="Pin message")
async def forward_message(interaction: discord.Interaction, message: discord.Message):
    if not interaction.guild_id:
        await interaction.response.send_message(
            "This command must be used in a server."
        )
        return

    mapping_data = get_channel_mapping(interaction.guild_id)
    if not mapping_data:
        await interaction.response.send_message(
            "Please use `/set_forward_channel` first"
        )
        return

    # Get the cog to use its helper method
    cog = interaction.client.get_cog("MessageUtilityCommands")
    if not cog:
        await interaction.response.send_message("Message utility commands not loaded.")
        return

    channel = await cog._get_channel_from_id(mapping_data.channel_id)
    if not channel:
        await interaction.response.send_message(
            "Forward channel not found. It may have been deleted."
        )
        return

    await interaction.response.send_message(f"Forwarded to {channel.mention}")
    await channel.send(
        f"**Forwarded message from {message.author.mention}:**\n{message.content}"
    )
    logger.info(f"Forwarded message {message.id} to channel {channel.id}")


# --- Setup function ---


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageUtilityCommands(bot))
    bot.tree.add_command(reprint)
    bot.tree.add_command(forward_message)
