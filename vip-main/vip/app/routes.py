from flask import render_template, request, redirect, session, url_for, flash, jsonify, current_app
from .models import db, Application, Article, TeamMember, Service, can_submit_application, get_application_stats
from .forms import ApplicationForm, AdminLoginForm, ArticleForm, ServiceForm
from .utils.helpers import (
    SecurityHelper, NotificationHelper, 
    RateLimitHelper, LoggingHelper
)
from functools import wraps
import os
from datetime import datetime
from . import cache

def admin_required(f):
    """Декоратор для проверки авторизации админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Требуется авторизация', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_app(app):
    @app.route('/')
    @cache.cached(timeout=300)  # Кэшируем на 5 минут
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
    @cache.cached(timeout=600)  # Кэшируем на 10 минут
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
    @cache.cached(timeout=600)  # Кэшируем на 10 минут
    def services():
        """Страница услуг"""
        services_list = Service.query.filter_by(is_active=True).order_by(Service.order_index).all()
        return render_template('services.html', services=services_list)

    @app.route('/contacts', methods=['GET', 'POST'])
    def contacts():
        """Страница контактов с формой заявки"""
        form = ApplicationForm()
        
        if request.method == 'POST' and form.validate_on_submit():
            try:
                # Получение IP адреса
                ip_address = SecurityHelper.get_client_ip()
                
                # Проверка ограничений
                if not RateLimitHelper.check_rate_limit(form.phone.data, app.config['SUBMISSION_LIMIT_MINUTES']):
                    flash(f'Вы можете отправлять заявки не чаще чем раз в {app.config["SUBMISSION_LIMIT_MINUTES"]} минут.', 'warning')
                    return redirect(url_for('contacts'))
                
                if not RateLimitHelper.check_rate_limit(ip_address, app.config['SUBMISSION_LIMIT_MINUTES']):
                    flash(f'Слишком много запросов с вашего IP. Попробуйте позже.', 'warning')
                    return redirect(url_for('contacts'))
                
                # Создание заявки
                application = Application(
                    name=form.name.data.strip(),
                    phone=form.phone.data.strip(),
                    email=form.email.data.strip() if form.email.data else None,
                    service_type=form.service_type.data if form.service_type.data else None,
                    message=form.message.data.strip() if form.message.data else None,
                    ip_address=ip_address
                )
                
                db.session.add(application)
                db.session.commit()
                
                # Логирование
                LoggingHelper.log_application_submission(application.to_dict())
                
                # Отправка уведомлений
                notification_text = NotificationHelper.format_application_notification(application.to_dict())
                NotificationHelper.send_telegram_notification(notification_text)
                
                flash('Ваша заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.', 'success')
                return redirect(url_for('contacts'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating application: {e}")
                flash('Произошла ошибка при отправке заявки. Попробуйте позже.', 'error')
        
        elif request.method == 'POST':
            # Если форма не прошла валидацию, показываем ошибки
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
        
        return render_template('contacts.html', form=form)

    @app.route('/blog')
    @cache.cached(timeout=300)  # Кэшируем на 5 минут
    def blog():
        """Страница блога"""
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('POSTS_PER_PAGE', 10)
        
        articles = Article.query.order_by(Article.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('blog.html', articles=articles)

    @app.route('/article/<slug>')
    @cache.cached(timeout=300)  # Кэшируем на 5 минут
    def article(slug):
        """Страница отдельной статьи"""
        article = Article.query.filter_by(slug=slug).first_or_404()
        
        # Получаем связанные статьи
        related_articles = Article.query.filter(
            Article.id != article.id,
            Article.is_featured == True
        ).order_by(Article.created_at.desc()).limit(3).all()
        
        return render_template('article.html', article=article, related_articles=related_articles)

    # API маршруты перенесены в отдельные модули

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Админ панель"""
        stats = get_application_stats()
        recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', stats=stats, recent_applications=recent_applications)

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Страница входа в админ-панель"""
        if session.get('admin_logged_in'):
            return redirect(url_for('admin_dashboard'))
        
        form = AdminLoginForm()
        
        if request.method == 'POST' and form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            
            if (username == current_app.config['ADMIN_USERNAME'] and 
                SecurityHelper.verify_password(password, current_app.config['ADMIN_PASSWORD'])):
                session['admin_logged_in'] = True
                session.permanent = True
                flash('Вы успешно вошли в систему', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')
                LoggingHelper.log_security_event('failed_login', f'Failed login attempt for username: {username}')
        
        return render_template('admin_login.html', form=form)

    @app.route('/admin/logout')
    def admin_logout():
        """Выход из админ-панели"""
        session.pop('admin_logged_in', None)
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
        
        flash('Заявка помечена как обработанная', 'success')
        return redirect(url_for('view_application', app_id=app_id))

    @app.route('/admin/applications')
    @admin_required
    def list_applications():
        """Список всех заявок"""
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '')
        
        query = Application.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        applications = query.order_by(Application.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        return render_template('applications.html', applications=applications, status_filter=status_filter)

    # Health check перенесен в API модуль