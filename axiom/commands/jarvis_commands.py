import discord
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


def load_system_prompt() -> dict:
    """Load the system prompt from the JSON file specified in the .env."""
    path = config.get("JARVIS_SYSTEM_PROMPT_PATH", "jarvis_system_prompt.json")
    if not os.path.isfile(path):
        logger.error(f"System prompt file not found: {path}")
        return {"role": "system", "content": "You are a helpful assistant."}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class JarvisCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jarvis = OpenRouterClient(api_key=config.get("OPENROUTER_API_KEY"))
        self.system_prompt = load_system_prompt()

    @app_commands.command(name="jarvis")
    @app_commands.describe(query="The message to send to Jarvis")
    async def invoke_jarvis(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)

        # Add user message to history
        user_message = JarvisMessage.create_user_message(query)
        add_jarvis_message(user_message)

        # Get message history and prepend system prompt
        message_history = get_jarvis_history()
        full_history = [self.system_prompt] + message_history

        # Get response from AI
        try:
            response = self.jarvis.get_completion(
                model="meta-llama/llama-3.3-8b-instruct:free", messages=full_history
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
