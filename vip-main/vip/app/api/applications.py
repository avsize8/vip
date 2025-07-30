from flask import request, jsonify, current_app
from . import api_v1
from ..models import db, Application
from ..utils.helpers import SecurityHelper, NotificationHelper, RateLimitHelper, LoggingHelper
from ..forms import ApplicationForm
from datetime import datetime

@api_v1.route('/applications', methods=['POST'])
def submit_application():
    """API для отправки заявок"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Валидация данных
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Name and phone are required'}), 400
        
        # Проверка ограничений
        ip_address = SecurityHelper.get_client_ip()
        if not RateLimitHelper.check_rate_limit(data['phone'], current_app.config['SUBMISSION_LIMIT_MINUTES']):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        if not RateLimitHelper.check_rate_limit(ip_address, current_app.config['SUBMISSION_LIMIT_MINUTES']):
            return jsonify({'error': 'IP rate limit exceeded'}), 429
        
        # Создание заявки
        application = Application(
            name=data['name'].strip(),
            phone=data['phone'].strip(),
            email=data.get('email', '').strip() if data.get('email') else None,
            service_type=data.get('service_type'),
            message=data.get('message', '').strip() if data.get('message') else None,
            ip_address=ip_address
        )
        
        db.session.add(application)
        db.session.commit()
        
        # Логирование
        LoggingHelper.log_application_submission(application.to_dict())
        
        # Отправка уведомлений
        notification_text = NotificationHelper.format_application_notification(application.to_dict())
        NotificationHelper.send_telegram_notification(notification_text)
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'id': application.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API Error creating application: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_v1.route('/applications', methods=['GET'])
def get_applications():
    """API для получения списка заявок (только для админов)"""
    # Здесь должна быть проверка авторизации
    # Пока возвращаем ошибку
    return jsonify({'error': 'Authentication required'}), 401

@api_v1.route('/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    """API для получения конкретной заявки"""
    # Здесь должна быть проверка авторизации
    return jsonify({'error': 'Authentication required'}), 401

@api_v1.route('/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    """API для обновления заявки"""
    # Здесь должна быть проверка авторизации
    return jsonify({'error': 'Authentication required'}), 401

@api_v1.route('/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    """API для удаления заявки"""
    # Здесь должна быть проверка авторизации
    return jsonify({'error': 'Authentication required'}), 401 