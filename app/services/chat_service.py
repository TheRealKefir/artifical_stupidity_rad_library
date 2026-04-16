from app.models import User, Chat, Message, Book
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


class ChatService:
    @staticmethod
    def get_user_chats(user_id):
        chats = db.session.query(Chat).filter(Chat.user_id == user_id).all()
        return chats

    @staticmethod
    def get_chat_messages(chat_id):
        messages = db.session.query(Message).filter(Message.chat_id == chat_id).all()
        return messages

    @staticmethod
    def delete_chat_message(chat_id, message_id):
        message = db.session.query(Message).filter(Message.chat_id == message_id).first()
        db.session.delete(Message).where(Message.timestamp > message.timestamp and Message.chat_id == chat_id)
        db.session.delete(message)
        db.session.commit()
        logger.info(f'Message with chat_id {chat_id} deleted')
        return ChatService.get_chat_messages(chat_id)

    @staticmethod
    def delete_chat(chat_id):
        chat = db.session.query(Chat).filter(Chat.id == chat_id).first()
        db.session.delete(chat)
        db.session.commit()
        logger.info(f'Chat with chat_id {chat_id} deleted')
        return ChatService.get_user_chats(chat_id)

    @staticmethod
    def create_chat(user_id):
        chat = Chat(user_id=user_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        logger.info(f'Chat with chat_id {chat.id} created')
        return chat

    @staticmethod
    def send_chat_message(chat_id, message):
        pass


