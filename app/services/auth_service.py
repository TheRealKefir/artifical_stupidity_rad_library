from app.models.user import User
from app.extensions import db
import bcrypt
import logging


logger = logging.getLogger(__name__)


class AuthService:
    """
    Сервис для управления аутентификацией и пользователями.
    Инкапсулирует логику работы с БД и хеширования.
    """

    @staticmethod
    def register_user(username, email, password):
        if not username or not email or not password:
            logger.warning("Попытка регистрации с пустыми полями")
            raise ValueError("Все поля обязательны для заполнения")

        existing_user = db.session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            logger.warning(f"Попытка регистрации с уже существующим username/email: {username}/{email}")
            raise ValueError("Пользователь с таким именем или email уже существует")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()
        logger.info(f"Новый пользователь зарегистрирован: {username} ({email})")
        return new_user

    @staticmethod
    def login_user(username, password):
        if not username or not password:
            logger.warning("Попытка входа с пустыми полями")
            raise ValueError("Все поля обязательны для заполнения")
        user = db.session.query(User).filter(
            (User.username == username)).first()
        if not user:
            logger.warning(f"Попытка входа с несуществующим username: {username}")
            raise ValueError("Неверное имя пользователя или пароль")
        if not user.verify_password(password):
            logger.warning(f"Попытка входа с неверным паролем для username: {username}")
            raise ValueError("Неверное имя пользователя или пароль")
        logger.info(f"Пользователь успешно вошел: {username}")
        return user
