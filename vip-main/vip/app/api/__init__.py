from flask import Blueprint

# Создаем Blueprint для API v1
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Импортируем все маршруты API
from . import applications, health 