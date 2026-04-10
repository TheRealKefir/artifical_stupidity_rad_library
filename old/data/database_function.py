import os

from .models import User, Chat, Message
from .session import get_db, Session
from .exceptions import *
import bcrypt


def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_user_by_id(user_id: int) -> User:
    db = get_db()
    return db.query.get(user_id)


def login_user(email: str, password: str) -> User:
    db = next(get_db())
    user = db.query.filter_by(email=email).first()
    if not user:
        raise NotFound(f'User with email {email} not found')
    if User.verify_password(user, password):
        return user
    else:
        raise IncorrectPassword('Incorrect password')


def register_user(username: str, email: str, password: str) -> User:
    db = next(get_db())
    if db.query(User).filter_by(username=username):
        raise UserExists(f'User with username {username} already exists')
    if db.query(User).filter_by(email=email):
        raise UserExists(f'User with email {email} already exists')
    user = User(username=username,
                email=email,
                password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    user.user_db = "/db/chroma/user_{}".format(user.id)
    db.commit()
    db.refresh(user)
    return user


def update_username(user_id: int, new_username: str):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    user.username = new_username
    db.commit()
    db.refresh(user)


def update_email(user_id: int, new_email: str):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    if db.query(User).filter_by(email=new_email):
        raise EmailExists(f"Email {new_email} already exists")
    user.email = new_email
    db.commit()
    db.refresh(user)


def update_password(user_id: int, new_password: str):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    user.password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)


def get_user_chats(user_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chats = db.query(Chat).filter_by(user_id=user.id).all()
    return chats


def get_chat_messages(user_id: int, chat_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = db.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        raise ChatNotExists(f'Chat with id {chat_id} not found')
    if chat.user_id != user.id:
        raise ChatAccessForbidden(f'Chat with id {chat_id} not allowed')
    messages = db.query(Message).filter_by(chat_id=chat.id)
    return messages


def get_chat(user_id: int, chat_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = db.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        raise ChatNotExists(f'Chat with id {chat_id} not found')
    if chat.user_id != user.id:
        raise ChatAccessForbidden(f'Chat with id {chat_id} not allowed')
    return chat


def create_chat(user_id: int, chat_name: str = None):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = Chat(name=chat_name, user_id=user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def delete_chat(chat_id: int, user_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = db.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        raise ChatNotExists(f'Chat with id {chat_id} not found')
    if chat.user_id != user.id:
        raise ChatAccessForbidden(f'Chat with id {chat_id} not allowed')
    chat.messages = db.query(Message).filter_by(chat_id=chat.id).all()
    for message in chat.messages:
        db.session.delete(message)
    db.session.delete(chat)
    db.commit()


def new_message(chat_id: int, user_id: int, content: str, sender: str):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = db.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        raise ChatNotExists(f'Chat with id {chat_id} not found')
    if chat.user_id != user.id:
        raise ChatAccessForbidden(f'Chat with id {chat_id} not allowed')
    message = Message(chat_id=chat.id, user_id=user.id, content=content, sender=sender)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def delete_message(chat_id: int, user_id: int, message_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    chat = db.query(Chat).filter_by(id=chat_id).first()
    if not chat:
        raise ChatNotExists(f'Chat with id {chat_id} not found')
    if chat.user_id != user.id:
        raise ChatAccessForbidden(f'Chat with id {chat_id} not allowed')
    message = db.query(Message).filter_by(id=message_id).first()
    db.session.delete(Message).filter_by(chat_id=chat.id).where(Message.timestamp > message.timestamp).all()
    db.session.delete(message)
    db.commit()


def delete_user(user_id: int):
    db = next(get_db())
    user = get_user_by_id(user_id)
    if not user:
        raise NotFound(f'User with id {user_id} not found')
    db.delete(user)
    db.commit()


def drop_user_db(user_id: int):
    user_db = "/db/chroma/user_{}".format(user_id)
    os.remove(user_db)
