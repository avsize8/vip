# Юридическая компания - Веб-приложение

Современное веб-приложение для юридической компании с системой управления заявками, Telegram ботом и админ-панелью.

## 🚀 Возможности

- **Веб-сайт компании** с информативными страницами
- **Система заявок** с валидацией и ограничениями
- **Telegram бот** для уведомлений и управления
- **Админ-панель** для обработки заявок
- **API** для интеграции с внешними системами
- **Система логирования** и мониторинга
- **Безопасность** с валидацией и защитой от спама

## 🛠 Технологии

- **Backend**: Flask 3.1.0, SQLAlchemy 2.0
- **База данных**: SQLite
- **Telegram API**: python-telegram-bot 20.0
- **Валидация**: Регулярные выражения и кастомные валидаторы
- **Безопасность**: Хеширование паролей, CSRF защита
- **Логирование**: RotatingFileHandler

## 📋 Требования

- Python 3.8+
- pip
- Telegram Bot Token
- Email сервер (опционально)

## 🔧 Установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd vip
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка конфигурации**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. **Создание базы данных**
```bash
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.create_all()"
```

## ⚙️ Конфигурация

Создайте файл `.env` со следующими переменными:

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# База данных
DATABASE=instance/applications.db

# Telegram бот
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Email (опционально)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com

# Админ учетные данные
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Ограничения
SUBMISSION_LIMIT_MINUTES=15
```

## 🚀 Запуск

### Веб-приложение
```bash
python wsgi.py
```
Приложение будет доступно по адресу: http://localhost:5000

### Telegram бот
```bash
python telegram_bot.py
```

### Docker (опционально)
```bash
docker-compose up -d
```

## 📱 Использование

### Веб-сайт
- **Главная страница**: Обзор услуг и команды
- **О компании**: Информация о компании и статистика
- **Услуги**: Подробное описание юридических услуг
- **Контакты**: Форма отправки заявки
- **Блог**: Статьи и новости

### Админ-панель
- Доступ: `/admin`
- Просмотр и обработка заявок
- Статистика и аналитика
- Управление контентом

### Telegram бот
Команды бота:
- `/start` - Главное меню
- `/help` - Справка
- `/stats` - Статистика заявок
- `/new` - Новые заявки
- `/all` - Все заявки

## 🔒 Безопасность

### Валидация данных
- Проверка формата телефона и email
- Валидация имени пользователя
- Ограничение длины сообщений
- Санитизация пользовательского ввода

### Защита от спама
- Ограничение количества заявок по времени
- Проверка по IP адресу и телефону
- Логирование подозрительной активности

### Аутентификация
- Хеширование паролей с солью
- Сессии с защищенными ключами
- Логирование попыток входа

## 📊 API

### Отправка заявки
```http
POST /api/applications
Content-Type: application/json

{
    "name": "Иван Иванов",
    "phone": "+79001234567",
    "email": "ivan@example.com",
    "service_type": "Банкротство",
    "message": "Нужна консультация"
}
```

### Ответ
```json
{
    "success": true,
    "id": 123,
    "message": "Application submitted successfully"
}
```

## 🗂 Структура проекта

```
vip/
├── app/
│   ├── __init__.py          # Конфигурация приложения
│   ├── models.py            # Модели данных (SQLAlchemy)
│   ├── routes.py            # Маршруты и контроллеры
│   ├── utils/
│   │   └── helpers.py       # Утилиты и хелперы
│   ├── static/              # Статические файлы
│   └── templates/           # HTML шаблоны
├── docker/                  # Docker конфигурация
├── logs/                    # Логи приложения
├── instance/                # База данных
├── telegram_bot.py          # Telegram бот
├── wsgi.py                  # Точка входа
└── requirements.txt         # Зависимости
```

## 🧪 Тестирование

```bash
# Установка тестовых зависимостей
pip install pytest pytest-flask

# Запуск тестов
pytest

# Покрытие кода
pytest --cov=app
```

## 📝 Логирование

Логи сохраняются в файл `logs/app.log` с ротацией:
- Максимальный размер файла: 10MB
- Количество резервных копий: 5
- Уровни логирования: DEBUG, INFO, WARNING, ERROR

## 🔧 Разработка

### Добавление новых услуг
1. Отредактируйте функцию `create_default_services()` в `models.py`
2. Перезапустите приложение

### Добавление новых полей в заявку
1. Обновите модель `Application` в `models.py`
2. Добавьте валидацию в `ValidationHelper`
3. Обновите шаблоны и API

### Кастомизация уведомлений
1. Отредактируйте `NotificationHelper.format_application_notification()`
2. Настройте шаблоны email в `NotificationHelper.send_email()`

## 🐛 Устранение неполадок

### Проблемы с базой данных
```bash
# Удаление и пересоздание БД
rm instance/applications.db
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import db; db.create_all()"
```

### Проблемы с Telegram ботом
- Проверьте токен бота в `.env`
- Убедитесь, что бот добавлен в чат
- Проверьте права бота на отправку сообщений

### Проблемы с email
- Проверьте настройки SMTP сервера
- Для Gmail используйте App Password
- Проверьте настройки TLS/SSL

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📞 Поддержка

При возникновении проблем создайте Issue в репозитории или обратитесь к разработчику. 