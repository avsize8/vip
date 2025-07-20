import pytest
from app import create_app
from app.models import db, Application, Service, TeamMember
from datetime import datetime

@pytest.fixture
def app():
    """Создание тестового приложения"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()

class TestApplication:
    """Тесты для модели Application"""
    
    def test_create_application(self, app):
        """Тест создания заявки"""
        with app.app_context():
            application = Application(
                name='Иван Иванов',
                phone='+79001234567',
                email='ivan@example.com',
                service_type='Банкротство',
                message='Нужна консультация'
            )
            db.session.add(application)
            db.session.commit()
            
            assert application.id is not None
            assert application.name == 'Иван Иванов'
            assert application.status == 'new'
    
    def test_phone_validation(self, app):
        """Тест валидации телефона"""
        with app.app_context():
            # Валидный номер
            assert Application.validate_phone('+79001234567') == True
            assert Application.validate_phone('89001234567') == True
            
            # Невалидные номера
            assert Application.validate_phone('123') == False
            assert Application.validate_phone('abc') == False
            assert Application.validate_phone('') == False
    
    def test_email_validation(self, app):
        """Тест валидации email"""
        with app.app_context():
            # Валидные email
            assert Application.validate_email('test@example.com') == True
            assert Application.validate_email('') == True  # Email не обязателен
            
            # Невалидные email
            assert Application.validate_email('invalid-email') == False
            assert Application.validate_email('test@') == False

class TestService:
    """Тесты для модели Service"""
    
    def test_create_service(self, app):
        """Тест создания услуги"""
        with app.app_context():
            service = Service(
                name='Банкротство',
                description='Профессиональное сопровождение процедур банкротства',
                icon='balance-scale',
                order_index=1
            )
            db.session.add(service)
            db.session.commit()
            
            assert service.id is not None
            assert service.name == 'Банкротство'
            assert service.is_active == True

class TestTeamMember:
    """Тесты для модели TeamMember"""
    
    def test_create_team_member(self, app):
        """Тест создания члена команды"""
        with app.app_context():
            member = TeamMember(
                name='Александр Петров',
                position='Управляющий партнер',
                bio='Более 15 лет опыта',
                experience=15,
                order_index=1
            )
            db.session.add(member)
            db.session.commit()
            
            assert member.id is not None
            assert member.name == 'Александр Петров'
            assert member.is_active == True 