import os
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager
from app.utils.logging import setup_logger


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    setup_logger(app)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    # раскоментить когда появятся блюпринты
    # from app.blueprints.auth import auth_bp
    # from app.blueprints.library import library_bp
    # from app.blueprints.chat import chat_bp

    # app.register_blueprint(auth_bp, url_prefix='/auth')
    # app.register_blueprint(library_bp, url_prefix='/library')
    # app.register_blueprint(chat_bp, url_prefix='/chat')

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.logger.info("Приложение Flask успешно запущено")

    return app