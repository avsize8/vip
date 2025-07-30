from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import event, Index
from sqlalchemy.orm import relationship
import re

# Используем db из __init__.py
from . import db

class Application(db.Model):
    """Модель заявки"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(120), index=True)
    service_type = db.Column(db.String(50), index=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default='new', index=True)
    ip_address = db.Column(db.String(45), index=True)
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('idx_phone_created', 'phone', 'created_at'),
        Index('idx_ip_created', 'ip_address', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Application {self.id}: {self.name}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'service_type': self.service_type,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'ip_address': self.ip_address
        }
    
    @staticmethod
    def validate_phone(phone):
        """Валидация номера телефона"""
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        return bool(phone_pattern.match(phone.replace(' ', '').replace('-', '')))
    
    @staticmethod
    def validate_email(email):
        """Валидация email"""
        if not email:
            return True
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(email))

class Article(db.Model):
    """Модель статьи"""
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    slug = db.Column(db.String(200), unique=True, index=True)
    
    # Индексы для оптимизации
    __table_args__ = (
        Index('idx_featured_created', 'is_featured', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Article {self.id}: {self.title}>'
    
    def generate_slug(self):
        """Генерация slug из заголовка"""
        import unicodedata
        slug = unicodedata.normalize('NFKD', self.title)
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug

class TeamMember(db.Model):
    """Модель члена команды"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    image = db.Column(db.String(255))
    experience = db.Column(db.Integer)  # опыт в годах
    is_active = db.Column(db.Boolean, default=True, index=True)
    order_index = db.Column(db.Integer, default=0, index=True)  # для сортировки
    
    def __repr__(self):
        return f'<TeamMember {self.id}: {self.name}>'

class Service(db.Model):
    """Модель услуги"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50))
    slug = db.Column(db.String(50), unique=True, index=True)  # Добавляем slug для идентификации
    is_active = db.Column(db.Boolean, default=True, index=True)
    order_index = db.Column(db.Integer, default=0, index=True)
    
    def __repr__(self):
        return f'<Service {self.id}: {self.name}>'

def can_submit_application(phone, ip_address, limit_minutes=15):
    """Проверяет лимит на отправку заявок"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=limit_minutes)
    
    recent_application = Application.query.filter(
        (Application.phone == phone) | (Application.ip_address == ip_address),
        Application.created_at > cutoff_time
    ).first()
    
    return recent_application is None

def get_application_stats():
    """Получение статистики заявок"""
    total = Application.query.count()
    new = Application.query.filter_by(status='new').count()
    processed = Application.query.filter_by(status='processed').count()
    
    return {
        'total': total,
        'new': new,
        'processed': processed,
        'pending': total - new - processed
    }

def init_app(app):
    """Инициализация базы данных"""
    with app.app_context():
        db.create_all()
        
        # Создание базовых данных если таблицы пустые
        if not Service.query.first():
            create_default_services()
        
        if not TeamMember.query.first():
            create_default_team()

def create_default_services():
    """Создание услуг по умолчанию"""
    services = [
        {
            'name': 'Банкротство',
            'description': 'Профессиональное сопровождение процедур банкротства физических и юридических лиц.',
            'icon': 'balance-scale',
            'slug': 'bankruptcy',
            'order_index': 1
        },
        {
            'name': 'Споры по недвижимости',
            'description': 'Юридическое сопровождение сделок с недвижимостью и разрешение споров.',
            'icon': 'home',
            'slug': 'real-estate',
            'order_index': 2
        },
        {
            'name': 'Административные споры',
            'description': 'Защита интересов в спорах с государственными органами.',
            'icon': 'gavel',
            'slug': 'administrative',
            'order_index': 3
        },
        {
            'name': 'Налоговые споры',
            'description': 'Помощь в налоговых спорах и оптимизация налогообложения.',
            'icon': 'calculator',
            'slug': 'tax',
            'order_index': 4
        },
        {
            'name': 'Корпоративное право',
            'description': 'Юридическое сопровождение бизнеса и корпоративные споры.',
            'icon': 'building',
            'slug': 'corporate',
            'order_index': 5
        },
        {
            'name': 'Семейные споры',
            'description': 'Решение семейных споров и вопросов наследования.',
            'icon': 'heart',
            'slug': 'family',
            'order_index': 6
        }
    ]
    
    for service_data in services:
        service = Service(**service_data)
        db.session.add(service)
    
    db.session.commit()

def create_default_team():
    """Создание команды по умолчанию"""
    team_members = [
        {
            'name': 'Александр Петров',
            'position': 'Управляющий партнер',
            'bio': 'Более 15 лет опыта в корпоративном праве и банкротстве.',
            'experience': 15,
            'order_index': 1
        },
        {
            'name': 'Мария Сидорова',
            'position': 'Старший юрист',
            'bio': 'Специалист по налоговым спорам и административному праву.',
            'experience': 12,
            'order_index': 2
        },
        {
            'name': 'Дмитрий Козлов',
            'position': 'Юрист',
            'bio': 'Эксперт по семейному праву и спорам о недвижимости.',
            'experience': 8,
            'order_index': 3
        }
    ]
    
    for member_data in team_members:
        member = TeamMember(**member_data)
        db.session.add(member)
    
    db.session.commit()

# События для автоматической генерации slug
@event.listens_for(Article, 'before_insert')
def generate_slug_before_insert(mapper, connection, target):
    if not target.slug:
        target.slug = target.generate_slug()