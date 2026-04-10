from functools import wraps
from flask import request, abort
from flask_login import current_user

def check_ownership(model):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resource_id = None
            for k, v in request.args.items():
                if k.endswith('_id'):
                    resource_id = v
                    break
            if resource_id is None:
                abort(500, description="No id found in route")
            resource = model.query.filter_by(id=resource_id).first()
            if resource is None:
                abort(404, description="No resource id provided")
            if resource.user_id != current_user.id:
                abort(403, description="You are not allowed to perform this action")
            kwargs['resource'] = resource
            return func(*args, **kwargs)
        return wrapper
    return decorator