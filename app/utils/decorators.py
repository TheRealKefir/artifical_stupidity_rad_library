from functools import wraps
from flask import abort
from flask_login import current_user
from app.extensions import db


def check_ownership(model, id_arg):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resource_id = kwargs.get(id_arg)
            if not resource_id:
                abort(400, description=f"Параметр {id_arg} не найден в роуте")
            resource = db.session.get(model, resource_id)
            if resource is None:
                abort(404, description="Ресурс не найден")
            if resource.user_id != current_user.id:
                abort(403, description="У вас нет прав доступа к этому ресурсу")
            return func(*args, **kwargs)

        return wrapper

    return decorator
