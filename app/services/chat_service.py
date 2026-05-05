from app.models import User, Chat, Message
from app.extensions import db
import logging
from langchain_core.messages import HumanMessage, AIMessage
from app.services import RagService
from app.services import AIService

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
        db.session.add(chat)
        db.session.commit()
        db.session.refresh(chat)
        logger.info(f'Chat with chat_id {chat.id} created')
        return chat

    @staticmethod
    def save_message(chat_id, user_id, role, content):
        try:
            new_message = Message(
                chat_id=chat_id,
                role=role,
                content=content,
                user_id=user_id
            )
            db.session.add(new_message)
            db.session.commit()
            db.session.refresh(new_message)
            logger.debug(f"Saved {role} message to chat {chat_id}")
            return new_message
        except Exception as e:
            db.session.rollback()
            logger.error(f"Save message error: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_chat_history(chat_id, limit=10):
        try:
            messages = db.session.query(Message).filter_by(chat_id=chat_id) \
                .order_by(Message.timestamp.asc()) \
                .limit(limit) \
                .all()

            history = []
            for msg in messages:
                if msg.role == 'user':
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    history.append(AIMessage(content=msg.content))
            return history
        except Exception as e:
            logger.error(f"History fetch error: {e}")
            return []

    @staticmethod
    def process_ai_response(chat_id, user_id):
        try:
            history = ChatService.get_chat_history(chat_id)
            if not history:
                return None

            last_query = history[-1].content

            vector_db = RagService.get_vector_db()
            relevant_docs = RagService.vector_search(
                query_text=last_query,
                db=vector_db,
                user_id=user_id,
                k=4
            )

            answer = AIService.generate_answer(
                query=last_query,
                context_documents=relevant_docs,
                chat_history=history[:-1]
            )

            return ChatService.save_message(chat_id, None, 'assistant', answer)

        except Exception as e:
            logger.error(f"AI Processing error: {str(e)}", exc_info=True)
            return ChatService.save_message(chat_id, None, 'assistant', "Произошла техническая ошибка при генерации.")
