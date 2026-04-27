from functools import wraps
from flask import request, abort
from flask_login import current_user


def check_ownership(model):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            source = kwargs or request.view_args or {}

            resource_id = None
            for k, v in source.items():
                if k.endswith("_id"):
                    resource_id = v
                    break

            if resource_id is None:
                abort(400, description="No id found in route")

            resource = model.query.get(resource_id)

            if resource is None:
                abort(404)

            if resource.user_id != current_user.id:
                abort(403)

            return func(*args, **kwargs)

        return wrapper

    return decorator
