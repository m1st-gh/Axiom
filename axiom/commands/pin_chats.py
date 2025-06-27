import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from axiom.database import db
from axiom.models import PinChannel


class PinChats(commands.Cog):
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

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Please use this command in a text channel."
            )
            return

        with db.get_session() as session:
            stmt = insert(PinChannel).values(
                guild_id=interaction.guild_id, channel_id=interaction.channel_id
            )

            stmt = stmt.on_conflict_do_update(
                index_elements=["guild_id"], set_={"channel_id": interaction.channel_id}
            )

            session.execute(stmt)
            session.commit()

        await interaction.response.send_message(
            f"Forward channel has been set to {interaction.channel.mention}"
        )


# --- Context Menu Commands (must be at module level) ---
@app_commands.context_menu(name="Pin message")
async def forward_message(interaction: discord.Interaction, message: discord.Message):
    if not interaction.guild_id:
        await interaction.response.send_message(
            "This command must be used in a server."
        )
        return

    with db.get_session() as session:
        stmt = select(PinChannel).where(PinChannel.guild_id == interaction.guild_id)
        if (channel := session.scalar(stmt)) is None:
            await interaction.response.send_message(
                "Please use `/set_forward_channel` first"
            )
            return

    if not (channel := interaction.client.get_channel(channel)):
        await interaction.response.send_message(
            "Forward channel not found. It may have been deleted."
        )
        return
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("Forward channel is invalid.")
        return

    await interaction.response.send_message(f"Forwarded to {channel.mention}")
    await channel.send(
        f"**Forwarded message from {message.author.mention}:**\n{message.content}"
    )


# --- Setup function ---


async def setup(bot: commands.Bot):
    await bot.add_cog(PinChats(bot))
    bot.tree.add_command(forward_message)
