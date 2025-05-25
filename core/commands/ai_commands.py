import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
import json
import os

from core import logger
from core.apis.client import OpenRouterClient
from core.database.schema import ChatMessage
from core.database.handlers import add_chat_message, get_chat_history
from core.config import config


def load_prompt(env_var: str) -> dict:
    """
    Load the prompt from the JSON file specified by the given environment variable.
    If the file does not exist, returns a default prompt.
    """
    path = config.get(env_var)
    if not path:
        logger.error(f"Environment variable '{env_var}' is not set.")
        return {"role": "system", "content": "You are a helpful assistant."}
    if not os.path.isfile(path):
        logger.error(f"System prompt file not found: {path}")
        return {"role": "system", "content": "You are a helpful assistant."}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai_client = OpenRouterClient(api_key=config.get("OPENROUTER_API_KEY"))
        self.system_prompt = load_prompt("AI_SYSTEM_PROMPT_PATH")
        self.summary_prompt = load_prompt("AI_SUMMARY_PROMPT_PATH")
        self.ai_model = config.get("AI_MODEL", "meta-llama/llama-4-scout:free")
        self.max_tokens = int(config.get("AI_MAX_TOKENS", "250"))

    @app_commands.command(name="summary")
    async def summarize_channel(self, interaction: discord.Interaction):
        """Ask Jarvis to summarize the last 200 messages."""
        await interaction.response.defer(thinking=True)
        if interaction.channel_id is not None:
            channel = self.bot.get_channel(interaction.channel_id)
        messages = [message async for message in channel.history(limit=200)]

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
        current_time_message = {
            "role": "system",
            "content": f"The current system time is: {now}",
        }

        # Compose the full history
        full_history = [self.summary_prompt, current_time_message] + message_history

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
            logger.info("AI responded to summary request")

        except Exception as e:
            logger.error(f"Error in AI summary command: {str(e)}")
            await interaction.followup.send(f"Error: {str(e)}")

    @app_commands.command(name="ask")
    @app_commands.describe(query="Your question for the AI assistant")
    async def ask_ai(self, interaction: discord.Interaction, query: str):
        """Ask the AI assistant, Javis a question"""
        await interaction.response.defer(thinking=True)

        # Add user message to history
        user_message = ChatMessage.create_user_message(query)
        add_chat_message(user_message)

        # Get message history and prepend system prompt
        message_history = get_chat_history()
        full_history = [self.system_prompt] + message_history

        # Get response from AI
        try:
            response = self.ai_client.get_completion(
                model=self.ai_model,
                messages=full_history,
                max_tokens=self.max_tokens,
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
            logger.info(f"AI responded to query: {query[:30]}...")

        except Exception as e:
            logger.error(f"Error in AI command: {str(e)}")
            await interaction.followup.send(f"Error: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))
