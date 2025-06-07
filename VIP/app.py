from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # Загрузка переменных окружения

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())
# Конфигурация
app.config['DATABASE'] = 'instance/applications.db'
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL')

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                service_type TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new'
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_featured BOOLEAN DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                bio TEXT,
                image TEXT,
                experience INTEGER,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        db.commit()
        db.close()

def send_email(subject, body, to_email):
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

@app.route('/')
def index():
    db = get_db_connection()
    featured_articles = db.execute('SELECT * FROM articles WHERE is_featured = 1 ORDER BY created_at DESC LIMIT 3').fetchall()
    team_members = db.execute('SELECT * FROM team_members WHERE is_active = 1 LIMIT 4').fetchall()
    db.close()
    return render_template('index.html', featured_articles=featured_articles, team_members=team_members)

@app.route('/about')
def about():
    db = get_db_connection()
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
            'details': 'Мы предлагаем полный спектр услуг по сопровождению процедуры банкротства...'
        },
        {
            'id': 'real-estate',
            'title': 'Споры по недвижимости',
            'icon': 'home',
            'description': 'Решение любых вопросов, связанных с недвижимостью и земельными отношениями.',
            'details': 'Наши юристы помогут разрешить спорные ситуации...'
        },
        {
            'id': 'administrative',
            'title': 'Административные споры',
            'icon': 'gavel',
            'description': 'Защита интересов клиентов в отношениях с государственными органами.',
            'details': 'Представительство в судах и государственных органах...'
        },
        {
            'id': 'tax',
            'title': 'Налоговые споры',
            'icon': 'calculator',
            'description': 'Защита в налоговых спорах и оптимизация налогообложения.',
            'details': 'Помощь в разрешении споров с налоговыми органами...'
        },
        {
            'id': 'corporate',
            'title': 'Корпоративное право',
            'icon': 'building',
            'description': 'Сопровождение корпоративных сделок и разрешение споров.',
            'details': 'Юридическое сопровождение бизнеса на всех этапах...'
        },
        {
            'id': 'family',
            'title': 'Семейные споры',
            'icon': 'heart',
            'description': 'Решение семейных споров и раздел имущества.',
            'details': 'Помощь в разрешении семейных конфликтов...'
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
        
        if not name or not phone:
            flash('Пожалуйста, заполните обязательные поля (имя и телефон)', 'danger')
            return redirect(url_for('contacts'))
        
        try:
            # Проверяем существование директории для базы данных
            os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)
            
            db = get_db_connection()
            cursor = db.cursor()
            
            # Проверяем существование таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                init_db()  # Если таблицы нет, инициализируем базу данных
            
            # Вставляем данные
            cursor.execute('''
                INSERT INTO applications (name, phone, email, service_type, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, phone, email, service_type, message))
            db.commit()
            
            # Отправка уведомления администратору
            if app.config['ADMIN_EMAIL']:
                email_body = f'''
                Новая заявка с сайта:
                Имя: {name}
                Телефон: {phone}
                Email: {email}
                Услуга: {service_type or 'Не указана'}
                Сообщение: {message or 'Не указано'}
                '''
                send_email('Новая заявка с сайта', email_body, app.config['ADMIN_EMAIL'])
            
            flash('Ваша заявка принята! Мы свяжемся с вами в ближайшее время.', 'success')
            
        except sqlite3.Error as e:
            db.rollback()
            flash('Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.', 'danger')
            app.logger.error(f"Database error: {e}")
            
        except Exception as e:
            flash('Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.', 'danger')
            app.logger.error(f"Error in contacts route: {e}")
            
        finally:
            if 'db' in locals():
                db.close()
            
        return redirect(url_for('contacts'))
    
    return render_template('contacts.html')

@app.route('/blog')
def blog():
    db = get_db_connection()
    articles = db.execute('SELECT * FROM articles ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('blog.html', articles=articles)

@app.route('/article/<int:article_id>')
def article(article_id):
    db = get_db_connection()
    article = db.execute('SELECT * FROM articles WHERE id = ?', (article_id,)).fetchone()
    if not article:
        db.close()
        flash('Статья не найдена', 'danger')
        return redirect(url_for('blog'))
    
    related_articles = db.execute('''
        SELECT * FROM articles 
        WHERE id != ? 
        ORDER BY RANDOM() 
        LIMIT 3
    ''', (article_id,)).fetchall()
    db.close()
    return render_template('article.html', article=article, related_articles=related_articles)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
