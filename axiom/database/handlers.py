from typing import List, Optional, Dict, Any
from tinydb import TinyDB, Query
from datetime import datetime

from axiom import logger
from axiom.database.schema import PinChannel, JarvisMessage
from axiom.config import config

# Get DB path from config (which loads from .env)
DB_PATH = config.get("AXIOM_DB_PATH", "axiom_db.json")
db = TinyDB(DB_PATH)
pin_channels_table = db.table("pin_channels")
jarvis_messages_table = db.table("jarvis_messages")


def set_pin_channel(guild_id: int, channel_id: int) -> None:
    Guild = Query()
    pin_channel = PinChannel(guild_id=guild_id, channel_id=channel_id)
    pin_channels_table.upsert(pin_channel.to_dict(), Guild.guild_id == guild_id)
    logger.info(f"Set pin channel {channel_id} for guild {guild_id}")


def get_pin_channel(guild_id: int) -> Optional[PinChannel]:
    Guild = Query()
    result = pin_channels_table.search(Guild.guild_id == guild_id)
    if not result:
        return None
    return PinChannel.from_dict(result[0])


def add_jarvis_message(message: JarvisMessage) -> int:
    doc_id = jarvis_messages_table.insert(message.to_dict())
    logger.debug(f"Added message to Jarvis history: {message.content[:50]}...")
    return doc_id


def get_jarvis_history() -> List[Dict[str, Any]]:
    messages = jarvis_messages_table.all()
    current_time = datetime.now().timestamp()
    to_remove = []
    for message in messages:
        if message["timestamp"] < current_time - 3600:
            to_remove.append(message.doc_id)
    if to_remove:
        jarvis_messages_table.remove(doc_ids=to_remove)
        logger.debug(f"Cleaned up {len(to_remove)} old Jarvis messages")
        messages = jarvis_messages_table.all()
    return messages
