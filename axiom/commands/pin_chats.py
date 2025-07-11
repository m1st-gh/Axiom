import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from axiom import logger
from axiom.database import db
from axiom.models import PinChannel


class PinChats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _set_pin_channel(self, session: Session, guild_id: int, channel_id: int):
        stmt = insert(PinChannel).values(guild_id=guild_id, channel_id=channel_id)
        stmt = stmt.on_conflict_do_update(
            index_elements=["guild_id"], set_={"channel_id": channel_id}
        )
        session.execute(stmt)
        session.commit()
        logger.info(f"Set pin channel for guild {guild_id} to {channel_id}")

    def _get_pin_channel(self, session: Session, guild_id: int) -> int | None:
        stmt = select(PinChannel).where(PinChannel.guild_id == guild_id)
        if (channel := session.scalar(stmt)) is not None:
            return channel.channel_id
        return None

    @app_commands.command(
        name="set_forward_channel",
        description="Set the current channel for forwarding pinned messages",
    )
    async def set_forward_channel_cmd(self, interaction: discord.Interaction):
        logger.info(
            f"User {interaction.user} in guild {interaction.guild} used /set_forward_channel in channel {interaction.channel}"
        )
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command must be used in a server."
            )
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Please use this command in a text channel."
            )
            return

        with db.get_session() as session:
            self._set_pin_channel(session, interaction.guild_id, interaction.channel_id)

        await interaction.response.send_message(
            f"Forward channel has been set to {interaction.channel.mention}"
        )


@app_commands.context_menu(name="Pin message")
async def forward_message(interaction: discord.Interaction, message: discord.Message):
    logger.info(
        f"User {interaction.user} in guild {interaction.guild} used 'Pin message' on message {message.id} in channel {message.channel}"
    )
    if not interaction.guild_id:
        await interaction.response.send_message(
            "This command must be used in a server."
        )
        return

    with db.get_session() as session:
        cog = interaction.client.get_cog("PinChats")
        if not cog:
            logger.error("PinChats cog not found.")
            await interaction.response.send_message(
                "An unexpected error occurred.", ephemeral=True
            )
            return
        channel_id = cog._get_pin_channel(session, interaction.guild_id)
    if not channel_id:
        await interaction.response.send_message(
            "Please use `/set_forward_channel` first"
        )
        return

    channel = interaction.client.get_channel(channel_id)
    if not channel:
        logger.warning(f"Forward channel not found for guild {interaction.guild_id}")
        await interaction.response.send_message(
            "Forward channel not found. It may have been deleted."
        )
        return
    if not isinstance(channel, discord.TextChannel):
        logger.warning(
            f"Forward channel {channel.id} for guild {interaction.guild_id} is not a text channel"
        )
        await interaction.response.send_message("Forward channel is invalid.")
        return

    await interaction.response.send_message(f"Forwarded to {channel.mention}")
    await channel.send(
        f"**Pinned message from {message.author.mention}:**\n{message.content}"
    )


async def setup(bot: commands.Bot):
    await bot.add_cog(PinChats(bot))
    bot.tree.add_command(forward_message)
