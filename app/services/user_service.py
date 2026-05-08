from app.models.user import User
from app.extensions import db
from app.utils.helpers import get_user_by_id, get_password_hash
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def delete_user(user_id: int):
        user = db.session.query(User).filter(User.id == user_id).first()
        db.session.delete(user)
        db.session.commit()
        logger.info(f'User with email {user.email} deleted')

    @staticmethod
    def get_user_by_id(user_id: int):
        user = db.session.query(User).filter(User.id == user_id).first()
        return user

    @staticmethod
    def update_user(user_id: int, new_username: str, new_password: str, new_email: str):
        try:
            user = db.session.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User with id {user_id} not found")
                return False
            if new_username and new_username != user.username:
                user.username = new_username
            if new_email and new_email != user.email:
                user.email = new_email
            if new_password and get_password_hash(new_password) != user.password:
                user.password = get_password_hash(new_password)
            db.session.commit()
            logger.info(f'User with id {user_id} updated')
            return user

        except Exception as e:
            db.session.rollback()
            logger.error(f"Update user error: {e}")
            return False
