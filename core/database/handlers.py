from typing import List, Optional, Dict, Any
from tinydb import TinyDB, Query
from datetime import datetime

from core import logger
from core.database.schema import ChannelMapping, ChatMessage
from core.config import config

# Get DB path from config (which loads from .env)
DB_PATH = config.get("DB_PATH", "bot_db.json")
db = TinyDB(DB_PATH)
channel_mappings_table = db.table("channel_mappings")
chat_messages_table = db.table("chat_messages")


def set_channel_mapping(guild_id: int, channel_id: int) -> None:
    Guild = Query()
    channel_mapping = ChannelMapping(guild_id=guild_id, channel_id=channel_id)
    channel_mappings_table.upsert(channel_mapping.to_dict(), Guild.guild_id == guild_id)
    logger.info(f"Set mapping channel {channel_id} for guild {guild_id}")


def get_channel_mapping(guild_id: int) -> Optional[ChannelMapping]:
    Guild = Query()
    result = channel_mappings_table.search(Guild.guild_id == guild_id)
    if not result:
        return None
    return ChannelMapping.from_dict(result[0])


def add_chat_message(message: ChatMessage) -> int:
    doc_id = chat_messages_table.insert(message.to_dict())
    logger.debug(f"Added message to chat history: {message.content[:50]}...")
    return doc_id


def get_chat_history() -> List[Dict[str, Any]]:
    messages = chat_messages_table.all()
    current_time = datetime.now().timestamp()
    to_remove = []
    for message in messages:
        if message["timestamp"] < current_time - 3600:
            to_remove.append(message.doc_id)
    if to_remove:
        chat_messages_table.remove(doc_ids=to_remove)
        logger.debug(f"Cleaned up {len(to_remove)} old chat messages")
        messages = chat_messages_table.all()
    return messages
