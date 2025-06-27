import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from axiom.apis.orclient import OpenRouterClient
from axiom.config import config


class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai_client = OpenRouterClient(api_key=config.openrouter_api_token)

    @app_commands.command(name="summary")
    async def summarize_channel(self, interaction: discord.Interaction):
        """Ask Jarvis to summarize the last 200 messages."""
        await interaction.response.defer(thinking=True)
        if interaction.channel_id is not None:
            channel = self.bot.get_channel(interaction.channel_id)
        messages = [message async for message in channel.history(limit=25)]

        message_history = [
            ChatMessage.create_user_message(
                f"Time: {message.created_at}, User:{message.author}, Message: {message.content}"
            )
            for message in messages
        ]
        message_history = [
            {"role": msg.role, "content": msg.content} for msg in message_history
        ]

        # Append the current system time as a system message
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        current_time_message = f" The current system time is: {now}"

        self.summary_prompt["content"] += current_time_message
        # Compose the full history
        full_history = [self.summary_prompt] + message_history

        try:
            response = self.ai_client.get_completion(
                model=self.ai_model,
                messages=full_history,
                max_tokens=self.max_tokens,
            )

            if len(response) > 2000:
                response = response[:1999]

            await interaction.followup.send(
                response or "I couldn't generate a response."
            )

        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")

    @app_commands.command(name="ask")
    @app_commands.describe(query="Your question for the AI assistant")
    async def ask_ai(self, interaction: discord.Interaction, query: str):

        await interaction.response.defer(thinking=True)
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            # add return message
            return
        messages = [message async for message in channel.history(after=)]

        

        try:
            response = self.ai_client.get_completion(
                model=config.model,
                messages=,
                max_tokens=config.max_tokens,
            )

            # Save AI response to history
            if response:
                ai_message = ChatMessage(
                    role="assistant",
                    content=response,
                    timestamp=datetime.now().timestamp(),
                )
                add_chat_message(ai_message)

            if len(response) > 2000:
                response = response[:1999]

            await interaction.followup.send(
                response or "I couldn't generate a response."
            )

        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))
