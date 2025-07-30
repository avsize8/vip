import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import current_app, request
import logging

logger = logging.getLogger(__name__)

class SecurityHelper:
    """Класс для работы с безопасностью"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Генерация CSRF токена"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля с использованием bcrypt"""
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except ImportError:
            # Fallback к PBKDF2 если bcrypt недоступен
            salt = secrets.token_hex(16)
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"{salt}${hash_obj.hex()}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверка пароля"""
        try:
            import bcrypt
            # Пробуем bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except (ImportError, ValueError):
            # Fallback к PBKDF2
            try:
                salt, hash_hex = hashed.split('$')
                hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return hash_obj.hex() == hash_hex
            except (ValueError, AttributeError):
                return False
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Очистка пользовательского ввода"""
        if not text:
            return ""
        # Удаляем потенциально опасные символы
        text = re.sub(r'[<>"\']', '', text)
        return text.strip()
    
    @staticmethod
    def get_client_ip() -> str:
        """Получение реального IP клиента"""
        if request.headers.get('X-Forwarded-For'):
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                return forwarded_for.split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            real_ip = request.headers.get('X-Real-IP')
            if real_ip:
                return real_ip
        return request.remote_addr or 'unknown'
    
    @staticmethod
    def generate_secure_token() -> str:
        """Генерация безопасного токена"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Валидация CSRF токена"""
        return token == session_token and len(token) == 64

class ValidationHelper:
    """Класс для валидации данных"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация номера телефона"""
        if not phone:
            return False
        # Очищаем номер от пробелов и дефисов
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Проверяем формат: +7XXXXXXXXXX или 8XXXXXXXXXX
        pattern = r'^(\+7|8)[0-9]{10}$'
        return bool(re.match(pattern, clean_phone))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email"""
        if not email:
            return True  # Email не обязателен
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Валидация имени"""
        if not name or len(name.strip()) < 2:
            return False
        # Проверяем, что имя содержит только буквы, пробелы и дефисы
        pattern = r'^[а-яёА-ЯЁa-zA-Z\s\-]+$'
        return bool(re.match(pattern, name.strip()))
    
    @staticmethod
    def validate_message(message: str, max_length: int = 1000) -> bool:
        """Валидация сообщения"""
        if not message:
            return True  # Сообщение не обязателено
        return len(message.strip()) <= max_length

class NotificationHelper:
    """Класс для отправки уведомлений"""
    
    @staticmethod
    def send_email(subject: str, body: str, to_email: str, html_body: Optional[str] = None) -> bool:
        """Отправка email"""
        if not all([
            current_app.config.get('MAIL_SERVER'),
            current_app.config.get('MAIL_USERNAME'),
            current_app.config.get('MAIL_PASSWORD')
        ]):
            logger.warning("Email configuration is incomplete. Skipping email sending.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = current_app.config['MAIL_USERNAME']
            msg['To'] = to_email
            
            # Добавляем текстовую версию
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Добавляем HTML версию если есть
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            with smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT']) as server:
                if current_app.config.get('MAIL_USE_TLS'):
                    server.starttls()
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def send_telegram_notification(message: str, parse_mode: str = 'HTML') -> bool:
        """Отправка уведомления в Telegram"""
        if not all([
            current_app.config.get('TELEGRAM_BOT_TOKEN'),
            current_app.config.get('TELEGRAM_CHAT_ID')
        ]):
            logger.warning("Telegram configuration is incomplete. Skipping notification.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{current_app.config['TELEGRAM_BOT_TOKEN']}/sendMessage"
            payload = {
                'chat_id': current_app.config['TELEGRAM_CHAT_ID'],
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Telegram notification sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {e}")
            return False
    
    @staticmethod
    def format_application_notification(application_data: Dict[str, Any]) -> str:
        """Форматирование уведомления о заявке"""
        created_at = application_data.get('created_at')
        if isinstance(created_at, str):
            # Если это ISO формат, конвертируем в читаемый вид
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%d.%m.%Y %H:%M')
            except:
                pass
        
        return f"""
<b>📌 Новая заявка #{application_data['id']}</b>
━━━━━━━━━━━━━━
<b>📝 Имя:</b> {application_data['name']}
<b>📞 Телефон:</b> {application_data['phone']}
<b>📧 Email:</b> {application_data['email'] or 'Не указан'}
<b>🛠 Услуга:</b> {application_data['service_type'] or 'Не указана'}
<b>📋 Сообщение:</b> {application_data['message'] or 'Не указано'}
━━━━━━━━━━━━━━
<b>🌐 IP:</b> {application_data['ip_address']}
<b>📅 Дата:</b> {created_at}
        """

class RateLimitHelper:
    """Класс для работы с ограничениями"""
    
    @staticmethod
    def check_rate_limit(identifier: str, limit_minutes: int = 15) -> bool:
        """Проверка ограничения по времени"""
        from app.models import Application
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=limit_minutes)
        
        recent_application = Application.query.filter(
            (Application.phone == identifier) | (Application.ip_address == identifier),
            Application.created_at > cutoff_time
        ).first()
        
        return recent_application is None
    
    @staticmethod
    def get_rate_limit_info(identifier: str, limit_minutes: int = 15) -> Dict[str, Any]:
        """Получение информации об ограничениях"""
        from app.models import Application
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=limit_minutes)
        
        recent_applications = Application.query.filter(
            (Application.phone == identifier) | (Application.ip_address == identifier),
            Application.created_at > cutoff_time
        ).all()
        
        return {
            'can_submit': len(recent_applications) == 0,
            'recent_count': len(recent_applications),
            'limit_minutes': limit_minutes,
            'next_allowed': max([app.created_at for app in recent_applications]).replace(tzinfo=None) + timedelta(minutes=limit_minutes) if recent_applications else None
        }

class LoggingHelper:
    """Класс для логирования"""
    
    @staticmethod
    def log_application_submission(application_data: Dict[str, Any]):
        """Логирование отправки заявки"""
        logger.info(
            f"New application submitted: ID={application_data.get('id')}, "
            f"Name={application_data.get('name')}, Phone={application_data.get('phone')}, "
            f"IP={application_data.get('ip_address')}"
        )
    
    @staticmethod
    def log_security_event(event_type: str, details: str, ip_address: Optional[str] = None):
        """Логирование событий безопасности"""
        if not ip_address:
            ip_address = SecurityHelper.get_client_ip()
        
        logger.warning(
            f"Security event: {event_type} - {details} from IP: {ip_address}"
        )
    
    @staticmethod
    def log_performance_metric(metric_name: str, value: float, unit: str = 'ms'):
        """Логирование метрик производительности"""
        logger.info(f"Performance metric: {metric_name}={value}{unit}")
    
    @staticmethod
    def log_cache_hit(cache_key: str):
        """Логирование попаданий в кэш"""
        logger.debug(f"Cache hit: {cache_key}")
    
    @staticmethod
    def log_cache_miss(cache_key: str):
        """Логирование промахов кэша"""
        logger.debug(f"Cache miss: {cache_key}")
