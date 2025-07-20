import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select, Select
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Sequence

from axiom import logger
from axiom.apis.orclient import OpenRouterClient
from axiom.config import config
from axiom.database import db
from axiom.models import Message, User


class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.ai_client: OpenRouterClient = OpenRouterClient(
            api_key=config.openrouter_api_token
        )
        self.system_prompt: Optional[Dict[str, str]] = self._load_system_prompt()

    def _load_system_prompt(self) -> Optional[Dict[str, str]]:
        prompt_path: Optional[str] = config.prompts.get("chat_bot")
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
        user: Optional[User] = session.get(User, user_id)
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

    def _get_message_history(
        self, session: Session, user_id: int
    ) -> List[Dict[str, str]]:
        stmt: Select = select(Message).where(Message.user_id == user_id)
        messages: Sequence[Message] = session.execute(stmt).scalars().all()
        return [{"role": msg.role, "content": msg.message_content} for msg in messages]

    def _get_ai_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        response: Optional[str] = self.ai_client.get_completion(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=0.7,
        )
        if response is None:
            logger.error("Response is empty!")
            return None
        return response

    def _save_message(
        self, session: Session, user_id: int, role: str, content: str
    ) -> None:
        message: Message = Message(user_id=user_id, role=role, message_content=content)
        session.add(message)
        session.commit()

    async def _send_split_message(
        self, interaction: discord.Interaction, message: str
    ) -> None:
        logger.info(f"Sending message to {interaction.user} in {interaction.channel}")
        if len(message) <= 2000:
            await interaction.followup.send(content=message)
            return

        chunks: List[str] = []
        while len(message) > 0:
            if len(message) <= 2000:
                chunks.append(message)
                break

            # Process the first 2000 characters to find a split point
            chunk_to_check: str = message[:2000]

            # Find the last newline or period
            last_newline: int = chunk_to_check.rfind("\n")
            last_period: int = chunk_to_check.rfind(".")

            split_point: int = max(last_newline, last_period)

            # If no natural split point, force a split at 2000 characters
            if split_point == -1:
                split_point = 2000
            else:
                # Split after the punctuation mark
                split_point += 1

            chunks.append(message[:split_point])
            message = message[split_point:]

        for i, chunk in enumerate(chunks):
            if i == 0:
                await interaction.followup.send(content=chunk)
            else:
                await interaction.followup.send(content=chunk)

    @app_commands.command(name="ask")
    @app_commands.describe(query="Your question for the AI assistant")
    async def ask_ai(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer(thinking=True)
        logger.info(
            f"User {interaction.user} in guild {interaction.guild} used /ask with query: {query}"
        )

        user_id: int = interaction.user.id
        username: str = interaction.user.display_name

        with db.get_session() as session:
            user: User = self._get_or_create_user(session, user_id, username)
            self._save_message(session, user.user_id, "user", query)
            message_history: List[Dict[str, str]] = self._get_message_history(
                session, user.user_id
            )
            if self.system_prompt:
                message_history.insert(0, self.system_prompt)
            try:
                response: Optional[str] = self._get_ai_response(message_history)
                if response:
                    self._save_message(session, user.user_id, "assistant", response)
                    await self._send_split_message(interaction, response)
                else:
                    await interaction.followup.send("Sorry, I couldn't get a response.")

            except Exception as e:
                logger.error(f"Error getting completion from OpenRouter: {e}")
                await interaction.followup.send(f"Error: {str(e)}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AICommands(bot))
