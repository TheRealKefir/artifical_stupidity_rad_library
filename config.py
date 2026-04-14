import os


class Config:
    """Базовый класс конфигурации с общими настройками."""
    SECRET_KEY = '3a9e94207c18982b50b7334c7d47bfaa8e11f4064cdc7ace28ecc85fdbe735fe'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    HUGGING_FASE_API_KEY = 'пока нету'
    HF_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    HF_LLM_MODEL = "HuggingFaceH4/zephyr-7b-beta"

    VECTOR_STORE_PATH = os.path.join(BASE_DIR, 'instance', 'vector_db')

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'app/static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Конфигурация для сервера."""
    DEBUG = False