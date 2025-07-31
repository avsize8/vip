from flask import render_template, request, redirect, session, url_for, flash, jsonify, current_app
from .models import db, Application, Article, TeamMember, Service, can_submit_application, get_application_stats
from .utils.helpers import (
    ValidationHelper, SecurityHelper, NotificationHelper, 
    RateLimitHelper, LoggingHelper, ValidationError
)
from functools import wraps
import os
from datetime import datetime

def admin_required(f):
    """Декоратор для проверки авторизации админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Требуется авторизация', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_application_data(data):
    """Валидация данных заявки"""
    errors = []
    
    # Валидация имени
    if not ValidationHelper.validate_name(data.get('name', '')):
        errors.append('Имя должно содержать минимум 2 символа и только буквы')
    
    # Валидация телефона
    if not ValidationHelper.validate_phone(data.get('phone', '')):
        errors.append('Неверный формат номера телефона')
    
    # Валидация email
    if data.get('email') and not ValidationHelper.validate_email(data.get('email')):
        errors.append('Неверный формат email')
    
    # Валидация сообщения
    if data.get('message') and not ValidationHelper.validate_message(data.get('message')):
        errors.append('Сообщение слишком длинное (максимум 1000 символов)')
    
    if errors:
        raise ValidationError('; '.join(errors))

def init_app(app):
    @app.route('/')
    def index():
        """Главная страница"""
        featured_articles = Article.query.filter_by(is_featured=True).order_by(Article.created_at.desc()).limit(3).all()
        team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.order_index).limit(4).all()
        services = Service.query.filter_by(is_active=True).order_by(Service.order_index).all()
        
        return render_template('index.html', 
                             featured_articles=featured_articles, 
                             team_members=team_members,
                             services=services)

    @app.route('/about')
    def about():
        """Страница о компании"""
        team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.order_index).all()
        stats = {
            'cases': 250,
            'clients': 500,
            'years': 15,
            'awards': 12
        }
        return render_template('about.html', team_members=team_members, stats=stats)

    @app.route('/services')
    def services():
        """Страница услуг"""
        services_list = Service.query.filter_by(is_active=True).order_by(Service.order_index).all()
        return render_template('services.html', services=services_list)

    @app.route('/contacts', methods=['GET', 'POST'])
    def contacts():
        """Страница контактов с формой заявки"""
        if request.method == 'POST':
            try:
                # Получение и очистка данных
                form_data = {
                    'name': SecurityHelper.sanitize_input(request.form.get('name', '')),
                    'phone': SecurityHelper.sanitize_input(request.form.get('phone', '')),
                    'email': SecurityHelper.sanitize_input(request.form.get('email', '')),
                    'service_type': SecurityHelper.sanitize_input(request.form.get('service_type', '')),
                    'message': SecurityHelper.sanitize_input(request.form.get('message', ''))
                }
                
                # Валидация данных
                validate_application_data(form_data)
                
                # Получение IP адреса
                ip_address = SecurityHelper.get_client_ip()
                
                # Проверка ограничений
                if not RateLimitHelper.check_rate_limit(form_data['phone'], app.config['SUBMISSION_LIMIT_MINUTES']):
                    flash(f'Вы можете отправлять заявки не чаще чем раз в {app.config["SUBMISSION_LIMIT_MINUTES"]} минут.', 'warning')
                    return redirect(url_for('contacts'))
                
                if not RateLimitHelper.check_rate_limit(ip_address, app.config['SUBMISSION_LIMIT_MINUTES']):
                    flash(f'Слишком много заявок с вашего IP. Попробуйте позже.', 'warning')
                    return redirect(url_for('contacts'))
                
                # Создание заявки
                application = Application()
                application.name = form_data['name']
                application.phone = form_data['phone']
                application.email = form_data['email']
                application.service_type = form_data['service_type']
                application.message = form_data['message']
                application.ip_address = ip_address
                
                db.session.add(application)
                db.session.commit()
                
                # Логирование
                LoggingHelper.log_application_submission(application.to_dict())
                
                # Отправка уведомлений
                notification_data = application.to_dict()
                notification_data['created_at'] = datetime.now().strftime('%d.%m.%Y %H:%M')
                
                # Email уведомление
                if app.config.get('ADMIN_EMAIL'):
                    email_body = f"""
                    Новая заявка #{application.id}:
                    Имя: {application.name}
                    Телефон: {application.phone}
                    Email: {application.email or 'Не указан'}
                    Услуга: {application.service_type or 'Не указана'}
                    Сообщение: {application.message or 'Не указано'}
                    IP: {application.ip_address}
                    Дата: {application.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    NotificationHelper.send_email('Новая заявка', email_body, app.config['ADMIN_EMAIL'])
                
                # Telegram уведомление
                telegram_msg = NotificationHelper.format_application_notification(notification_data)
                NotificationHelper.send_telegram_notification(telegram_msg)
                
                flash('Ваша заявка принята! Мы свяжемся с вами в ближайшее время.', 'success')
                
            except ValidationError as e:
                flash(str(e), 'danger')
                return redirect(url_for('contacts'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error in contacts: {e}")
                flash('Произошла ошибка при отправке заявки. Попробуйте позже.', 'danger')
                return redirect(url_for('contacts'))
            
            return redirect(url_for('contacts'))
        
        services = Service.query.filter_by(is_active=True).order_by(Service.order_index).all()
        return render_template('contacts.html', services=services)

    @app.route('/blog')
    def blog():
        """Страница блога"""
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        articles = Article.query.order_by(Article.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('blog.html', articles=articles)

    @app.route('/article/<slug>')
    def article(slug):
        """Страница отдельной статьи"""
        article = Article.query.filter_by(slug=slug).first()
        if not article:
            flash('Статья не найдена', 'danger')
            return redirect(url_for('blog'))
        
        related_articles = Article.query.filter(
            Article.id != article.id
        ).order_by(db.func.random()).limit(3).all()
        
        return render_template('article.html', article=article, related_articles=related_articles)

    # API маршруты
    @app.route('/api/applications', methods=['POST'])
    def api_submit_application():
        """API для отправки заявки"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Валидация данных
            validate_application_data(data)
            
            # Проверка ограничений
            ip_address = SecurityHelper.get_client_ip()
            if not RateLimitHelper.check_rate_limit(data.get('phone', ''), app.config['SUBMISSION_LIMIT_MINUTES']):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Создание заявки
            application = Application()
            application.name = data['name']
            application.phone = data['phone']
            application.email = data.get('email')
            application.service_type = data.get('service_type')
            application.message = data.get('message')
            application.ip_address = ip_address
            
            db.session.add(application)
            db.session.commit()
            
            # Логирование и уведомления
            LoggingHelper.log_application_submission(application.to_dict())
            
            return jsonify({
                'success': True,
                'id': application.id,
                'message': 'Application submitted successfully'
            }), 201
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"API error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    # Админ маршруты
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Админ панель"""
        stats = get_application_stats()
        applications = Application.query.order_by(Application.created_at.desc()).limit(10).all()
        
        return render_template('dashboard.html', stats=stats, applications=applications)

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Страница входа в админ панель"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if (username == app.config.get('ADMIN_USERNAME') and 
                password == app.config.get('ADMIN_PASSWORD')):
                session['admin_logged_in'] = True
                session['admin_username'] = username
                flash('Вы успешно вошли в систему', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                LoggingHelper.log_security_event('failed_login', f'Failed login attempt for username: {username}')
                flash('Неверные учетные данные', 'danger')
        
        return render_template('admin_login.html')

    @app.route('/admin/logout')
    def admin_logout():
        """Выход из админ панели"""
        session.clear()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('admin_login'))

    @app.route('/admin/application/<int:app_id>')
    @admin_required
    def view_application(app_id):
        """Просмотр заявки"""
        application = Application.query.get_or_404(app_id)
        return render_template('view_application.html', application=application)

    @app.route('/admin/application/<int:app_id>/process')
    @admin_required
    def process_application(app_id):
        """Обработка заявки"""
        application = Application.query.get_or_404(app_id)
        application.status = 'processed'
        db.session.commit()
        
        flash('Заявка отмечена как обработанная', 'success')
        return redirect(url_for('view_application', app_id=app_id))

    @app.route('/admin/applications')
    @admin_required
    def list_applications():
        """Список всех заявок"""
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        per_page = 20
        
        query = Application.query
        if status:
            query = query.filter_by(status=status)
        
        applications = query.order_by(Application.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('applications_list.html', applications=applications)

    @app.route('/health')
    def health_check():
        """Health check endpoint для мониторинга"""
        try:
            # Проверка базы данных
            db.session.execute('SELECT 1')
            
            # Проверка Redis (если используется)
            if current_app.config.get('CACHE_TYPE') == 'redis':
                from flask_caching import Cache
                cache = Cache(current_app)
                cache.set('health_check', 'ok', timeout=10)
                cache.get('health_check')
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'cache': 'connected' if current_app.config.get('CACHE_TYPE') == 'redis' else 'not_configured'
            }), 200
        except Exception as e:
            current_app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500