# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 604800)))

    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123!')

    # Security
    BCRYPT_LOG_ROUNDS = 13
    CORS_ORIGINS = ['http://localhost', 'http://localhost:3000', 'http://cubinez.ru']

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'

    # === Email Settings ===
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1', 'yes')

    # Аутентификация SMTP (опционально — для вашего сервера может не требоваться)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # Например: cubinez85@cubinez.ru
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # Пароль или пусто если не требуется

    # Отправитель и получатель по умолчанию
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cubinez.ru')
    MAIL_RECIPIENT = os.environ.get('MAIL_RECIPIENT')  # Опционально: для тестов все письма сюда

    # Email verification settings
    EMAIL_VERIFICATION_EXPIRES_HOURS = int(os.environ.get('EMAIL_VERIFICATION_EXPIRES_HOURS', 24))
    EMAIL_VERIFICATION_MIN_INTERVAL_MINUTES = int(os.environ.get('EMAIL_VERIFICATION_MIN_INTERVAL_MINUTES', 5))

    # Base URL для генерации ссылок
    BASE_URL = os.environ.get('BASE_URL', 'https://auth.cubinez.ru')

    # Логирование писем вместо отправки (для разработки/тестов)
    MAIL_LOG_ONLY = os.environ.get('MAIL_LOG_ONLY', 'false').lower() in ('true', '1', 'yes')

    # === Password Reset Settings ===
    PASSWORD_RESET_EXPIRES_HOURS = int(os.environ.get('PASSWORD_RESET_EXPIRES_HOURS', 1))
    PASSWORD_RESET_MIN_INTERVAL_MINUTES = int(os.environ.get('PASSWORD_RESET_MIN_INTERVAL_MINUTES', 15))

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Конфигурация для тестов - БЕЗ pool_options для SQLite"""
    TESTING = True
    # SQLite in-memory для тестов
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'
    # ✅ Убираем pool_options для SQLite
    SQLALCHEMY_ENGINE_OPTIONS = {}
    # Отключаем rate limiting в тестах
    RATELIMIT_ENABLED = False
    # Упрощаем JWT для тестов
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
