from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()  # Загрузка переменных окружения

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

    # Конфигурация приложения
    app.config['TELEGRAM_BOT_TOKEN'] = os.getenv('TELEGRAM_BOT_TOKEN')
    app.config['TELEGRAM_CHAT_ID'] = os.getenv('TELEGRAM_CHAT_ID')
    app.config['DATABASE'] = 'instance/applications.db'
    app.config['SUBMISSION_LIMIT_MINUTES'] = 15

    # Импорт и регистрация модулей
    from . import models, routes
    models.init_app(app)
    routes.init_app(app)

    return app