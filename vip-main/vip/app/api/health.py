from flask import jsonify, current_app
from . import api_v1
from ..models import db
from .. import cache
from datetime import datetime

@api_v1.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья приложения"""
    try:
        # Проверяем подключение к БД
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Проверяем кэш
    try:
        cache.set('health_check', 'ok', timeout=10)
        cache_status = 'healthy' if cache.get('health_check') == 'ok' else 'unhealthy'
    except Exception as e:
        cache_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'database': db_status,
            'cache': cache_status
        }
    })

@api_v1.route('/status', methods=['GET'])
def status():
    """Расширенная информация о статусе"""
    from ..models import Application, Article, Service, TeamMember
    
    try:
        # Статистика базы данных
        stats = {
            'applications': Application.query.count(),
            'articles': Article.query.count(),
            'services': Service.query.count(),
            'team_members': TeamMember.query.count()
        }
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat(),
            'database_stats': stats,
            'config': {
                'debug': current_app.config.get('DEBUG', False),
                'environment': current_app.config.get('FLASK_ENV', 'development')
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500 