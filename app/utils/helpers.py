from app import db
from app.models.user import User
import uuid
import gc
import bcrypt
import torch


def generate_unic_name(filename):
    return uuid.uuid5(uuid.NAMESPACE_DNS, filename)


def allowed_file(filename):
    return filename.split('.')[-1].lower() == "txt"

def clear_hardware_cache():
    """
    Очищает оперативную память и видеопамять.
    """
    gc.collect()
    if torch.cuda.is_available():
        with torch.cuda.device('cuda'):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    gc.collect()

def get_user_by_id(user_id):
    """Вспомогательный метод для загрузчика Flask-Login."""
    return db.session.get(User, user_id)


def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')