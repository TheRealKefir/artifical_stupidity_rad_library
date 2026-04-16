from app.models.user import User
from app.extensions import db
from app.utils.helpers import get_user_by_id, get_password_hash
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def update_username(user_id: int, new_username: str):
        user = db.session.query(User).filter(User.id == user_id).first()
        user.username = new_username
        db.commit()
        db.refresh(user)
        logger.info(f'User with email {new_username} updated')
        return user

    @staticmethod
    def update_email(user_id: int, new_email: str):
        user = get_user_by_id(user_id)
        user.email = new_email
        db.commit()
        db.refresh(user)
        logger.info(f'User with email {new_email} updated')
        return user

    @staticmethod
    def update_password(user_id: int, new_password: str):
        user = get_user_by_id(user_id)
        user.password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        logger.info(f'User with email {new_password} updated')
        return user

    @staticmethod
    def delete_user(user_id: int):
        user = db.session.query(User).filter(User.id == user_id).first()
        db.session.delete(user)
        db.commit()
        logger.info(f'User with email {user.email} deleted')
