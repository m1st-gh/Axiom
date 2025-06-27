
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)

    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = 'messages'

    message_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    role = Column(String, nullable=False)
    message_content = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)

    user = relationship("User", back_populates="messages")

class PinChannel(Base):
    __tablename__ = 'pin_channels'

    guild_id = Column(Integer, primary_key=True, unique=True)
    channel_id = Column(Integer, nullable=False)
