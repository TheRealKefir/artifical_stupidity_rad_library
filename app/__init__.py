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

    from app.blueprints.root_routes import root_bp
    from app.blueprints.auth_routes import auth_bp
    from app.blueprints.chat_routes import chat_bp
    from app.blueprints.user_routes import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(root_bp)
    app.register_blueprint(user_bp)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    with app.app_context():
        db.create_all()
    app.logger.info("Приложение Flask успешно запущено")

    return app