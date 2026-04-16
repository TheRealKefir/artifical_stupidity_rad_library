from functools import wraps
from flask import jsonify, g
from app.models.chat import Chat
from app.extensions import db
import logging

logger = logging.getLogger(__name__)


def check_ownership(model_type):
    """
    роуты вида /chat/321/332 первый параметр Idшка чата
    """

    def decorator(f):
        @wraps(f)

        def decorated_function(*args, **kwargs):
            current_user = getattr(g, 'user', None)

            if not current_user:
                logger.warning("Попытка доступа без аутентификации")
                return jsonify({'error': 'Authentication required'}), 401

            if model_type == 'user':
                user_id = kwargs.get('user_id') or kwargs.get('id')

                if not user_id:
                    logger.error(f"ID пользователя не найден в kwargs: {kwargs}")
                    return jsonify({'error': 'User ID not provided'}), 400

                if current_user.id != user_id:
                    logger.warning(f"Пользователь {current_user.id} пытается получить доступ к пользователю {user_id}")
                    return jsonify({'error': 'Access denied'}), 403

            elif model_type == 'chat':
                chat_id = kwargs.get('chat_id') or kwargs.get('id')

                if not chat_id:
                    logger.error(f"ID чата не найден в kwargs: {kwargs}")
                    return jsonify({'error': 'Chat ID not provided'}), 400

                chat = db.session.query(Chat).filter(Chat.id == chat_id).first()

                if not chat:
                    logger.warning(f"Чат с ID {chat_id} не найден")
                    return jsonify({'error': 'Chat not found'}), 404

                # 
                if chat.user_id != current_user.id:
                    logger.warning(f"Пользователь {current_user.id} не является владельцем чата {chat_id}")
                    return jsonify({'error': 'Access denied to this chat'}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_current_user():
    """получениe текущего пользователя"""
    return getattr(g, 'user', None)
