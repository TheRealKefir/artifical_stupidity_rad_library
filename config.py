import os
from decouple import config


class Config:
    """Базовый класс конфигурации."""
    # Считываем секретный ключ, если его нет — используем заглушку (но лучше без неё)
    SECRET_KEY = config('SECRET_KEY', default='fallback-very-secret-key')

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Путь к БД: если в .env нет DATABASE_URL, собираем дефолтный sqlite
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL',
                                     default=f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки Celery (в Docker-compose мы используем адрес 'redis')
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

    # AI настройки
    HUGGING_FACE_API_KEY = config('HUGGING_FACE_API_KEY')
    HF_EMBEDDING_MODEL = config('HF_EMBEDDING_MODEL', default="intfloat/multilingual-e5-large")
    HF_LLM_MODEL = config('HF_LLM_MODEL', default="Qwen/Qwen3Guard-Gen-4B")

    # Векторная БД (путь через config, чтобы можно было легко менять в Docker)
    VECTOR_STORE_PATH = config('VECTOR_STORE_PATH',
                               default=os.path.join(BASE_DIR, 'instance', 'vector_db'))

    UPLOAD_FOLDER = os.path.join('uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = config('DEBUG', default=True, cast=bool)
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Конфигурация для сервера."""
    DEBUG = config('DEBUG', default=False, cast=bool)