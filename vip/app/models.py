import sqlite3
from datetime import datetime, timedelta

def get_db_connection(app):
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db(app):
    with app.app_context():
        db = get_db_connection(app)
        db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                service_type TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                ip_address TEXT
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

def can_submit_application(app, phone, ip_address):
    """Проверяет лимит на отправку заявок."""
    db = get_db_connection(app)
    try:
        last_submission = db.execute('''
            SELECT created_at FROM applications 
            WHERE phone = ? OR ip_address = ?
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (phone, ip_address)).fetchone()
        
        if last_submission:
            last_time = datetime.strptime(last_submission['created_at'], '%Y-%m-%d %H:%M:%S')
            return (datetime.now() - last_time) > timedelta(minutes=app.config['SUBMISSION_LIMIT_MINUTES'])
        return True
    finally:
        db.close()

def init_app(app):
    init_db(app)