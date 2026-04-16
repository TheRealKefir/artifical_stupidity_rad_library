from flask import Flask
from .auth_api import auth_bp
from .user_api import user_bp


def register_blueprints(app: Flask):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
