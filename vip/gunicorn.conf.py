# Gunicorn конфигурация для продакшена
import multiprocessing
import os

# Базовые настройки
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Таймауты
timeout = 30
keepalive = 2
graceful_timeout = 30

# Логирование
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Безопасность
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Перезапуск
preload_app = True
reload = False

# Пользователь и группа (если запускается от root)
# user = "appuser"
# group = "appuser"

# Переменные окружения
raw_env = [
    "FLASK_ENV=production",
]

def when_ready(server):
    """Вызывается когда сервер готов принимать соединения"""
    server.log.info("Gunicorn сервер готов к работе")

def on_starting(server):
    """Вызывается при запуске сервера"""
    server.log.info("Запуск Gunicorn сервера")

def on_exit(server):
    """Вызывается при завершении работы сервера"""
    server.log.info("Gunicorn сервер остановлен") 