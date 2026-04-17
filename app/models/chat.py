import datetime
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class Chat(db.Model):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    chat_name: Mapped[str] = mapped_column(String(120), nullable=True, default="Новый чат")
    last_activity: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)

    #messages = db.relationship("Message", back_populates="chat", cascade="all, delete-orphan", lazy="dynamic")


class Message(db.Model):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)
