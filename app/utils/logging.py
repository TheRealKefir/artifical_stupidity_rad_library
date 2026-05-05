import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(app):
    """
    Настройка логирования для Flask-приложения.
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s]: %(message)s'
    )
    file_handler = RotatingFileHandler(
        'logs/app.log', maxBytes=10485760, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info("Logging system initialized")