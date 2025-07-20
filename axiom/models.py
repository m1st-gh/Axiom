from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String, nullable=False)

    messages: Mapped[List["Message"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id"), nullable=True
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    message_content: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="messages")


class PinChannel(Base):
    __tablename__ = "pin_channels"

    guild_id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(nullable=False)
