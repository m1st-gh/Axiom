import discord
from discord import app_commands, message
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.orm import Session

from axiom import logger
from axiom.apis.orclient import OpenRouterClient
from axiom.config import config
from axiom.database import db
from axiom.models import Message, User


class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai_client = OpenRouterClient(api_key=config.openrouter_api_token)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self):
        prompt_path = config.prompts.get("chat_bot")
        if prompt_path:
            try:
                with open(prompt_path, "r") as f:
                    return {"role": "system", "content": f.read()}
            except FileNotFoundError:
                logger.warning(f"System prompt file not found at {prompt_path}")
        return None

    def _get_or_create_user(
        self, session: Session, user_id: int, username: str
    ) -> User:
        user = session.get(User, user_id)
        if user is None:
            logger.info(f"New user: {username} ({user_id})")
            user = User(user_id=user_id, username=username)
            session.add(user)
            session.commit()
        elif user.username != username:
            logger.info(
                f"User {user_id} changed username from {user.username} to {username}"
            )
            user.username = username
            session.commit()
        return user

    def _get_message_history(self, session: Session, user_id: int) -> list[dict]:
        stmt = select(Message).where(Message.user_id == user_id)
        messages = session.execute(stmt).scalars().all()
        return [{"role": msg.role, "content": msg.message_content} for msg in messages]

    def _get_ai_response(self, messages: list[dict]) -> str:
        return self.ai_client.get_completion(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=0.7,
        )

    def _save_message(self, session: Session, user_id: int, role: str, content: str):
        message = Message(user_id=user_id, role=role, message_content=content)
        session.add(message)
        session.commit()

    @app_commands.command(name="ask")
    @app_commands.describe(query="Your question for the AI assistant")
    async def ask_ai(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        logger.info(
            f"User {interaction.user} in guild {interaction.guild} used /ask with query: {query}"
        )

        user_id = interaction.user.id
        username = interaction.user.display_name

        with db.get_session() as session:
            user = self._get_or_create_user(session, user_id, username)
            self._save_message(session, user.user_id, "user", query)
            message_history = self._get_message_history(session, user.user_id)
            message_history.insert(0, self.system_prompt)
            try:
                response = self._get_ai_response(message_history)
                self._save_message(session, user.user_id, "assistant", response)
                await self._send_split_message(interaction, response)

            except Exception as e:
                logger.error(f"Error getting completion from OpenRouter: {e}")
                await interaction.followup.send(f"Error: {str(e)}")

    async def _send_split_message(self, interaction: discord.Interaction, message: str):
        logger.info(f"Sending message to {interaction.user} in {interaction.channel}")
        if len(message) <= 2000:
            await interaction.followup.send(content=message)
            return

        chunks = []
        current_chunk = ""
        lines = message.split("\n")

        for line in lines:
            if len(current_chunk) + len(line) + 1 > 2000:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                if len(line) > 2000:
                    words = line.split(" ")
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > 2000:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = ""
                        current_chunk += word + " "
                else:
                    current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        for i, chunk in enumerate(chunks):
            if i == 0:
                await interaction.followup.send(content=chunk)
            else:
                await interaction.followup.send(content=chunk)


async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))

