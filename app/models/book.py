from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db


class Book(db.Model):
    __tablename__ = 'book'
    book_id: Mapped[int] = db.Column(primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = db.Column(ForeignKey('user.id'), nullable=False)
    title: Mapped[str] = db.Column(db.String(255), nullable=False)
    filename: Mapped[str] = db.Column(db.String(255), nullable=False)
    author: Mapped[str] = db.Column(db.String(255), nullable=False)
    status: Mapped[str] = db.Column(db.String(255), nullable=False)
    embedding_model = db.Column(db.String(128))
