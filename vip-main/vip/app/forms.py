from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
import re

class ApplicationForm(FlaskForm):
    """Форма заявки"""
    name = StringField('Имя', validators=[
        DataRequired(message='Имя обязательно для заполнения'),
        Length(min=2, max=100, message='Имя должно содержать от 2 до 100 символов')
    ])
    
    phone = StringField('Телефон', validators=[
        DataRequired(message='Телефон обязателен для заполнения'),
        Length(min=10, max=20, message='Неверный формат номера телефона')
    ])
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Неверный формат email')
    ])
    
    service_type = SelectField('Услуга', validators=[
        Optional()
    ], choices=[
        ('', 'Выберите услугу'),
        ('bankruptcy', 'Банкротство'),
        ('real-estate', 'Споры по недвижимости'),
        ('administrative', 'Административные споры'),
        ('tax', 'Налоговые споры'),
        ('corporate', 'Корпоративное право'),
        ('family', 'Семейные споры'),
        ('other', 'Другое')
    ])
    
    message = TextAreaField('Сообщение', validators=[
        Optional(),
        Length(max=1000, message='Сообщение не должно превышать 1000 символов')
    ])
    
    submit = SubmitField('Отправить заявку')
    
    def validate_name(self, field):
        """Валидация имени - только буквы, пробелы и дефисы"""
        if field.data:
            pattern = r'^[а-яёА-ЯЁa-zA-Z\s\-]+$'
            if not re.match(pattern, field.data.strip()):
                raise ValidationError('Имя может содержать только буквы, пробелы и дефисы')
    
    def validate_phone(self, field):
        """Валидация номера телефона"""
        if field.data:
            # Очищаем номер от пробелов и дефисов
            clean_phone = re.sub(r'[\s\-\(\)]', '', field.data)
            # Проверяем формат: +7XXXXXXXXXX или 8XXXXXXXXXX
            pattern = r'^(\+7|8)[0-9]{10}$'
            if not re.match(pattern, clean_phone):
                raise ValidationError('Неверный формат номера телефона. Используйте формат: +7XXXXXXXXXX или 8XXXXXXXXXX')

class AdminLoginForm(FlaskForm):
    """Форма входа в админ-панель"""
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно')
    ])
    
    password = StringField('Пароль', validators=[
        DataRequired(message='Пароль обязателен')
    ])
    
    submit = SubmitField('Войти')

class ArticleForm(FlaskForm):
    """Форма для создания/редактирования статьи"""
    title = StringField('Заголовок', validators=[
        DataRequired(message='Заголовок обязателен'),
        Length(min=5, max=200, message='Заголовок должен содержать от 5 до 200 символов')
    ])
    
    content = TextAreaField('Содержание', validators=[
        DataRequired(message='Содержание обязательно'),
        Length(min=10, message='Содержание должно содержать минимум 10 символов')
    ])
    
    image = StringField('URL изображения', validators=[
        Optional()
    ])
    
    is_featured = SelectField('Рекомендуемая статья', choices=[
        (False, 'Нет'),
        (True, 'Да')
    ])
    
    submit = SubmitField('Сохранить')

class ServiceForm(FlaskForm):
    """Форма для создания/редактирования услуги"""
    name = StringField('Название услуги', validators=[
        DataRequired(message='Название обязательно'),
        Length(min=3, max=100, message='Название должно содержать от 3 до 100 символов')
    ])
    
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Описание обязательно'),
        Length(min=10, max=1000, message='Описание должно содержать от 10 до 1000 символов')
    ])
    
    icon = StringField('Иконка (FontAwesome класс)', validators=[
        Optional(),
        Length(max=50, message='Название иконки не должно превышать 50 символов')
    ])
    
    slug = StringField('Slug (URL)', validators=[
        Optional(),
        Length(max=50, message='Slug не должен превышать 50 символов')
    ])
    
    order_index = StringField('Порядок отображения', validators=[
        Optional()
    ])
    
    is_active = SelectField('Активна', choices=[
        (True, 'Да'),
        (False, 'Нет')
    ])
    
    submit = SubmitField('Сохранить') 