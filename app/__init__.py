import os
from flask import Flask
from config import Config
from app.extensions import db, migrate, login_manager
from app.utils.logging import setup_logger
# раскоментить когда появятся блюпринты
from app.blueprints.auth_api import auth_bp
from app.blueprints.main_api import main_bp



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    setup_logger(app)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
#
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.logger.info("Приложение Flask успешно запущено")

    return app