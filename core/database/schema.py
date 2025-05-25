from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class ChannelMapping:
    guild_id: int
    channel_id: int

    def to_dict(self) -> Dict[str, Any]:
        return {"guild_id": self.guild_id, "channel_id": self.channel_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChannelMapping":
        return cls(guild_id=data["guild_id"], channel_id=data["channel_id"])


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float
    doc_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], doc_id: Optional[int] = None
    ) -> "ChatMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            doc_id=doc_id,
        )

    @classmethod
    def create_user_message(cls, content: str) -> "ChatMessage":
        return cls(role="user", content=content, timestamp=datetime.now().timestamp())
