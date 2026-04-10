import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt
from .session import Base, engine

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    user_db: Mapped[str] = mapped_column(String(120), nullable=True)

    def verify_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_name: Mapped[str] = mapped_column(String(120), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_activity: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)
    user: Mapped["User"] = relationship("User", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)
    role: Mapped[str] = mapped_column(String(120), nullable=False)

    chat: Mapped["Chat"] = relationship("Chat", cascade="all, delete-orphan")
    user: Mapped["User"] = relationship("User", cascade="all, delete-orphan")

def create_tables():
    Base.metadata.create_all(engine)