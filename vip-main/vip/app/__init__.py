from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import render_template

load_dotenv()  # Загрузка переменных окружения

# Инициализация расширений
db = SQLAlchemy()
cache = Cache()
migrate = Migrate()

def create_app(config_name=None):
    """Фабрика приложений Flask"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    
    # Импорт конфигурации
    from config import config
    app.config.from_object(config[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    
    # Инициализация кэша только если он не отключен
    if app.config.get('CACHE_TYPE') != 'null':
        cache.init_app(app)
    
    migrate.init_app(app, db)
    
    # Настройка логирования
    setup_logging(app)
    
    # Создание директорий
    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
    os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
    
    # Импорт и регистрация модулей
    from . import models, routes
    models.init_app(app)
    routes.init_app(app)
    
    # Регистрация API Blueprint
    from .api import api_v1
    app.register_blueprint(api_v1)
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    return app

def setup_logging(app):
    """Настройка логирования"""
    if not app.debug and not app.testing:
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        # app.logger.info('Приложение запущено')  # Убираем лишнее сообщение

def register_error_handlers(app):
    """Регистрация обработчиков ошибок"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500