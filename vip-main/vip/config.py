import os
from datetime import timedelta

class Config:
    """Базовый класс конфигурации"""
    # Основные настройки Flask
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    
    # База данных
    DATABASE = os.getenv('DATABASE', 'instance/applications.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.abspath(DATABASE)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Telegram настройки
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Ограничения
    SUBMISSION_LIMIT_MINUTES = int(os.getenv('SUBMISSION_LIMIT_MINUTES', 15))
    
    # Email конфигурация
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    
    # Админ учетные данные
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Безопасность
    CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'true').lower() == 'true'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600)))
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Кэширование
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Пагинация
    POSTS_PER_PAGE = int(os.getenv('POSTS_PER_PAGE', 10))
    
    # Загрузка файлов
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CACHE_TYPE = 'simple'  # Используем простое кэширование в разработке

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    CSRF_ENABLED = True
    
    # Redis для кэширования в продакшене
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DATABASE = 'instance/test_applications.db'
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.abspath(DATABASE)}"
    CACHE_TYPE = 'null'
    WTF_CSRF_ENABLED = False

# Словарь конфигураций
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 