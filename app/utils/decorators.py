from functools import wraps
from flask import request, abort
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

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
                logger.info(f'Resource with id {resource_id} does not exist')
                abort(500, description="No id found in route")
            resource = model.query.filter_by(id=resource_id).first()
            if resource is None:
                logger.info(f'Resource with id {resource_id} does not exist')
                abort(404, description="No resource id provided")
            if resource.user_id != current_user.id:
                logger.info(f'User with id {current_user.id} does not own resource')
                abort(403, description="You are not allowed to perform this action")
            kwargs['resource'] = resource
            return func(*args, **kwargs)
        return wrapper
    return decorator