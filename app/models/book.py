from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class Book(db.Model):
    __tablename__ = 'book'
    book_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)  # user_id, не users_id
    # title: Mapped[str] = mapped_column(String(255), nullable=False)
    # filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # author: Mapped[str] = mapped_column(String(255), nullable=False)
    # status: Mapped[str] = mapped_column(String(255), nullable=False)
    # embedding_model = db.Column(db.String(128))
