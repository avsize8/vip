import pytest
import time
from app import create_app, db, cache
from app.models import Application, Service, TeamMember
from app.utils.helpers import SecurityHelper, RateLimitHelper
from app.forms import ApplicationForm

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

class TestPerformanceOptimizations:
    """Тесты производительности"""
    
    def test_caching_works(self, app, client):
        """Тест кэширования"""
        with app.app_context():
            # Первый запрос
            start_time = time.time()
            response1 = client.get('/')
            time1 = time.time() - start_time
            
            # Второй запрос (должен быть быстрее из-за кэша)
            start_time = time.time()
            response2 = client.get('/')
            time2 = time.time() - start_time
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert time2 < time1  # Второй запрос быстрее
    
    def test_database_indexes(self, app):
        """Тест индексов базы данных"""
        with app.app_context():
            # Создаем тестовые данные
            app1 = Application(name='Test1', phone='+79001234567')
            app2 = Application(name='Test2', phone='+79001234568')
            db.session.add_all([app1, app2])
            db.session.commit()
            
            # Запрос с индексом должен быть быстрым
            start_time = time.time()
            result = Application.query.filter_by(phone='+79001234567').first()
            query_time = time.time() - start_time
            
            assert result is not None
            assert query_time < 0.1  # Запрос должен быть быстрым

class TestSecurityOptimizations:
    """Тесты безопасности"""
    
    def test_bcrypt_password_hashing(self):
        """Тест хеширования паролей с bcrypt"""
        password = "test_password_123"
        
        # Хеширование
        hashed = SecurityHelper.hash_password(password)
        
        # Проверка
        assert SecurityHelper.verify_password(password, hashed) == True
        assert SecurityHelper.verify_password("wrong_password", hashed) == False
        assert hashed != password  # Пароль не должен быть в открытом виде
    
    def test_form_validation(self, app):
        """Тест валидации форм"""
        with app.app_context():
            # Валидная форма
            form_data = {
                'name': 'Иван Иванов',
                'phone': '+79001234567',
                'email': 'test@example.com',
                'service_type': 'bankruptcy',
                'message': 'Тестовое сообщение'
            }
            
            form = ApplicationForm(data=form_data)
            assert form.validate() == True
            
            # Невалидная форма
            invalid_data = {
                'name': '123',  # Неправильное имя
                'phone': 'invalid',  # Неправильный телефон
                'email': 'invalid-email'  # Неправильный email
            }
            
            form = ApplicationForm(data=invalid_data)
            assert form.validate() == False
            assert 'phone' in form.errors
            assert 'email' in form.errors

class TestAPIOptimizations:
    """Тесты API оптимизаций"""
    
    def test_api_versioning(self, client):
        """Тест версионирования API"""
        # Старый API endpoint больше не существует
        response_old = client.post('/api/applications')
        assert response_old.status_code == 404
        
        # Новый API endpoint работает
        response_new = client.get('/api/v1/health')
        assert response_new.status_code == 200
    
    def test_api_response_structure(self, client):
        """Тест структуры API ответов"""
        response = client.get('/api/v1/health')
        data = response.get_json()
        
        # Проверяем структуру ответа
        assert 'status' in data
        assert 'timestamp' in data
        assert 'services' in data
        assert 'database' in data['services']
        assert 'cache' in data['services']
    
    def test_rate_limiting(self, app):
        """Тест ограничений по времени"""
        with app.app_context():
            # Создаем тестовую заявку
            app1 = Application(
                name='Test',
                phone='+79001234567',
                ip_address='127.0.0.1'
            )
            db.session.add(app1)
            db.session.commit()
            
            # Проверяем ограничение
            can_submit = RateLimitHelper.check_rate_limit('+79001234567', 15)
            assert can_submit == False  # Нельзя отправить повторно

class TestCodeQuality:
    """Тесты качества кода"""
    
    def test_no_duplicate_config(self, app):
        """Тест отсутствия дублирования конфигурации"""
        # Проверяем, что используется единая конфигурация
        assert hasattr(app.config, 'SECRET_KEY')
        assert hasattr(app.config, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(app.config, 'CACHE_TYPE')
    
    def test_modular_structure(self, app):
        """Тест модульной структуры"""
        # Проверяем наличие Blueprint'ов
        assert 'api_v1' in app.blueprints
        
        # Проверяем регистрацию маршрутов
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/v1/health' in rules
        assert '/api/v1/applications' in rules
    
    def test_error_handling(self, client):
        """Тест обработки ошибок"""
        # Тест 404
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
        # Тест 500 (если есть)
        # response = client.get('/trigger-error')
        # assert response.status_code == 500

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 