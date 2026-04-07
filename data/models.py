import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import bcrypt

from .session import Base, engine


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    user_db: Mapped[str] = mapped_column(String(120))

    def verify_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    user_id: Mapped[int] = relationship("User", foreign_keys=[User.id])
    last_activity: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now())


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    chat_id: Mapped[int] = relationship("Chat", foreign_keys=[Chat.id])
    sender_id: Mapped[int] = relationship("User", foreign_keys=[User.id])
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now())


def create_tables():
    Base.metadata.create_all(engine)