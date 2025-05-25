import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os

from axiom import logger
from axiom.apis.orclient import OpenRouterClient
from axiom.database.schema import JarvisMessage
from axiom.database.handlers import add_jarvis_message, get_jarvis_history
from axiom.config import config


def load_system_prompt(env_var: str) -> dict:
    """
    Load the system prompt from the JSON file specified by the given environment variable.
    If the file does not exist, returns a default system prompt.
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


class JarvisCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jarvis = OpenRouterClient(api_key=config.get("OPENROUTER_API_KEY"))
        self.jarvis_prompt = load_system_prompt("JARVIS_SYSTEM_PROMPT_PATH")
        self.tldr_prompt = load_system_prompt("JARVIS_TLDR_PROMPT")

    @app_commands.command(name="tldr")
    async def invoke_tldr(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.channel_id is not None:
            channel = self.bot.get_channel(interaction.channel_id)
        messages = [message async for message in channel.history(limit=200)]

        message_history = [
            JarvisMessage.create_user_message(
                f"Time: {message.created_at}, User:{message.author}, Message: {message.content}"
            )
            for message in messages
        ]
        message_history = [
            {"role": msg.role, "content": msg.content} for msg in message_history
        ]

        # Load your system prompt as usual
        tldr_prompt = self.tldr_prompt  # or load from file if needed

        # Append the current system time as a system message
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        current_time_message = {
            "role": "system",
            "content": f"The current system time is: {now}",
        }

        # Compose the full history
        full_history = [tldr_prompt, current_time_message] + message_history

        try:
            response = self.jarvis.get_completion(
                model="meta-llama/llama-4-scout:free",
                messages=full_history,
                max_tokens=450,
            )

            await interaction.followup.send(
                response or "I couldn't generate a response."
            )
            logger.info("Jarvis responded to tldr...")

        except Exception as e:
            logger.error(f"Error in Jarvis command: {str(e)}")
            await interaction.followup.send(f"Error: {str(e)}")

    @app_commands.command(name="jarvis")
    @app_commands.describe(query="The message to send to Jarvis")
    async def invoke_jarvis(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        # Add user message to history
        user_message = JarvisMessage.create_user_message(query)
        add_jarvis_message(user_message)

        # Get message history and prepend system prompt
        message_history = get_jarvis_history()
        full_history = [self.jarvis_prompt] + message_history

        # Get response from AI
        try:
            response = self.jarvis.get_completion(
                model="meta-llama/llama-4-scout:free",
                messages=full_history,
                max_tokens=450,
            )

            # Save AI response to history
            if response:
                ai_message = JarvisMessage(
                    role="assistant",
                    content=response,
                    timestamp=datetime.now().timestamp(),
                )
                add_jarvis_message(ai_message)

            await interaction.followup.send(
                response or "I couldn't generate a response."
            )
            logger.info(f"Jarvis responded to query: {query[:30]}...")

        except Exception as e:
            logger.error(f"Error in Jarvis command: {str(e)}")
            await interaction.followup.send(f"Error: {str(e)}")


async def setup(bot: commands.Bot):
    await bot.add_cog(JarvisCommands(bot))
