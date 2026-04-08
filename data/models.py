import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import bcrypt
from .session import Base, engine

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    user_db: Mapped[str] = mapped_column(String(120), nullable=True)

    def verify_password(self, password: str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    chat_name: Mapped[str] = mapped_column(String(120), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_activity: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)

    user: Mapped["User"] = relationship("User")

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True, nullable=False, unique=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(nullable=False, default=datetime.datetime.now)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)

def create_tables():
    Base.metadata.create_all(engine)