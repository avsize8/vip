from flask import render_template, request, redirect, session, url_for, flash
from .models import get_db_connection, can_submit_application
import os
import smtplib
from email.mime.text import MIMEText
import requests
from datetime import datetime

def send_email(app, subject, body, to_email):
    if not all([app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
        app.logger.warning("Email configuration is incomplete. Skipping email sending.")
        return False
    
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = to_email
        
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            if app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Error sending email: {e}")
        return False

def send_telegram_notification(app, message):
    if not all([app.config['TELEGRAM_BOT_TOKEN'], app.config['TELEGRAM_CHAT_ID']]):
        app.logger.warning("Telegram configuration is incomplete. Skipping notification.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{app.config['TELEGRAM_BOT_TOKEN']}/sendMessage"
        payload = {
            'chat_id': app.config['TELEGRAM_CHAT_ID'],
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        app.logger.error(f"Error sending Telegram notification: {e}")
        return False

def init_app(app):
    @app.route('/')
    def index():
        db = get_db_connection(app)
        featured_articles = db.execute('SELECT * FROM articles WHERE is_featured = 1 ORDER BY created_at DESC LIMIT 3').fetchall()
        team_members = db.execute('SELECT * FROM team_members WHERE is_active = 1 LIMIT 4').fetchall()
        db.close()
        return render_template('index.html', featured_articles=featured_articles, team_members=team_members)

    @app.route('/about')
    def about():
        db = get_db_connection(app)
        team_members = db.execute('SELECT * FROM team_members WHERE is_active = 1').fetchall()
        stats = {
            'cases': 250,
            'clients': 500,
            'years': 15,
            'awards': 12
        }
        db.close()
        return render_template('about.html', team_members=team_members, stats=stats)

    @app.route('/services')
    def services():
        services_list = [
            {
                'id': 'bankruptcy',
                'title': 'Банкротство',
                'icon': 'balance-scale',
                'description': 'Профессиональное сопровождение процедур банкротства физических и юридических лиц.',
                'details': 'Мы предлагаем полный спектр услуг по сопровождению процедуры банкротства, включая консультации, подготовку документов и представительство в суде.'
            },
            {
                'id': 'real-estate',
                'title': 'Споры по недвижимости',
                'icon': 'home',
                'description': 'Юридическое сопровождение сделок с недвижимостью и разрешение споров.',
                'details': 'Помогаем решать любые вопросы, связанные с недвижимостью, включая споры о праве собственности и раздел имущества.'
            },
            {
                'id': 'administrative',
                'title': 'Административные споры',
                'icon': 'gavel',
                'description': 'Защита интересов в спорах с государственными органами.',
                'details': 'Представительство в административных делах и обжалование действий государственных органов.'
            },
            {
                'id': 'tax',
                'title': 'Налоговые споры',
                'icon': 'calculator',
                'description': 'Помощь в налоговых спорах и оптимизация налогообложения.',
                'details': 'Защита от неправомерных требований налоговых органов и сопровождение налоговых проверок.'
            },
            {
                'id': 'corporate',
                'title': 'Корпоративное право',
                'icon': 'building',
                'description': 'Юридическое сопровождение бизнеса и корпоративные споры.',
                'details': 'Помощь в корпоративных вопросах, включая регистрацию компаний и разрешение корпоративных конфликтов.'
            },
            {
                'id': 'family',
                'title': 'Семейные споры',
                'icon': 'heart',
                'description': 'Решение семейных споров и вопросов наследования.',
                'details': 'Помощь в семейных делах, включая расторжение брака, раздел имущества и определение места жительства детей.'
            }
        ]
        return render_template('services.html', services=services_list)

    @app.route('/contacts', methods=['GET', 'POST'])
    def contacts():
        if request.method == 'POST':
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            service_type = request.form.get('service_type')
            message = request.form.get('message')
            ip_address = request.remote_addr
            
            if not name or not phone:
                flash('Пожалуйста, заполните обязательные поля (имя и телефон)', 'danger')
                return redirect(url_for('contacts'))
            
            if not can_submit_application(app, phone, ip_address):
                flash(f'Вы можете отправлять заявки не чаще чем раз в {app.config["SUBMISSION_LIMIT_MINUTES"]} минут.', 'warning')
                return redirect(url_for('contacts'))
            
            try:
                os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
                db = get_db_connection(app)
                cursor = db.cursor()
                
                cursor.execute('''
                    INSERT INTO applications (name, phone, email, service_type, message, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, phone, email, service_type, message, ip_address))
                db.commit()
                
                app_id = cursor.lastrowid
                
                if app.config['ADMIN_EMAIL']:
                    email_body = f'''
                    Новая заявка #{app_id}:
                    Имя: {name}
                    Телефон: {phone}
                    Email: {email or 'Не указан'}
                    Услуга: {service_type or 'Не указана'}
                    Сообщение: {message or 'Не указано'}
                    IP: {ip_address}
                    Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    '''
                    send_email(app, 'Новая заявка', email_body, app.config['ADMIN_EMAIL'])
                
                telegram_msg = f"""
<b>📌 Новая заявка #{app_id}</b>
━━━━━━━━━━━━━━
<b>📝 Имя:</b> {name}
<b>📞 Телефон:</b> {phone}
<b>📧 Email:</b> {email or 'Не указан'}
<b>🛠 Услуга:</b> {service_type or 'Не указана'}
<b>📋 Сообщение:</b> {message or 'Не указано'}
━━━━━━━━━━━━━━
<b>🌐 IP:</b> {ip_address}
<b>📅 Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
                """
                send_telegram_notification(app, telegram_msg)
                
                flash('Ваша заявка принята!', 'success')
                
            except Exception as e:
                db.rollback()
                flash('Ошибка при сохранении данных.', 'danger')
                app.logger.error(f"Error in contacts: {e}")
                
            finally:
                db.close()
            
            return redirect(url_for('contacts'))
        
        return render_template('contacts.html')

    @app.route('/blog')
    def blog():
        db = get_db_connection(app)
        articles = db.execute('SELECT * FROM articles ORDER BY created_at DESC').fetchall()
        db.close()
        return render_template('blog.html', articles=articles)

    @app.route('/article/<int:article_id>')
    def article(article_id):
        db = get_db_connection(app)
        article = db.execute('SELECT * FROM articles WHERE id = ?', (article_id,)).fetchone()
        if not article:
            db.close()
            flash('Статья не найдена', 'danger')
            return redirect(url_for('blog'))
        
        related_articles = db.execute('SELECT * FROM articles WHERE id != ? ORDER BY RANDOM() LIMIT 3', (article_id,)).fetchall()
        db.close()
        return render_template('article.html', article=article, related_articles=related_articles)

    @app.route('/admin')
    def admin_dashboard():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        
        db = get_db_connection(app)
        stats = {
            'total': db.execute('SELECT COUNT(*) FROM applications').fetchone()[0],
            'new': db.execute('SELECT COUNT(*) FROM applications WHERE status = "new"').fetchone()[0],
            'processed': db.execute('SELECT COUNT(*) FROM applications WHERE status = "processed"').fetchone()[0]
        }
        applications = db.execute('SELECT * FROM applications ORDER BY created_at DESC LIMIT 10').fetchall()
        db.close()
        return render_template('dashboard.html', stats=stats, applications=applications)

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            if (request.form.get('username') == os.getenv('ADMIN_USERNAME') and 
                request.form.get('password') == os.getenv('ADMIN_PASSWORD')):
                session['admin_logged_in'] = True
                return redirect(url_for('admin_dashboard'))
            flash('Неверные учетные данные', 'danger')
        return render_template('admin_login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('admin_logged_in', None)
        return redirect(url_for('admin_login'))

    @app.route('/admin/application/<int:app_id>')
    def view_application(app_id):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        
        db = get_db_connection(app)
        application = db.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
        db.close()
        
        if not application:
            flash('Заявка не найдена', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        return render_template('view_application.html', application=application)

    @app.route('/admin/application/<int:app_id>/process')
    def process_application(app_id):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        
        db = get_db_connection(app)
        db.execute('UPDATE applications SET status = "processed" WHERE id = ?', (app_id,))
        db.commit()
        db.close()
        flash('Заявка обработана', 'success')
        return redirect(url_for('view_application', app_id=app_id))