import os


class Config:
    """Базовый класс конфигурации с общими настройками."""
    SECRET_KEY = '3a9e94207c18982b50b7334c7d47bfaa8e11f4064cdc7ace28ecc85fdbe735fe'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'

    HUGGING_FACE_API_KEY = ''
    HF_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    HF_LLM_MODEL = "HuggingFaceH4/zephyr-7b-beta"

    VECTOR_STORE_PATH = os.path.join(BASE_DIR, 'instance', 'vector_db')

    UPLOAD_FOLDER = os.path.join('uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Конфигурация для сервера."""
    DEBUG = False