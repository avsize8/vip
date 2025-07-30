# 🚀 Руководство по развертыванию в продакшене

## 📋 Предварительные требования

### Системные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Минимум 2GB (рекомендуется 4GB+)
- **CPU**: 2 ядра (рекомендуется 4+)
- **Диск**: 20GB свободного места
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Установка Docker и Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🔧 Настройка окружения

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd vip
```

### 2. Создание файла переменных окружения
```bash
cp env.production.example .env
```

### 3. Настройка переменных окружения
Отредактируйте файл `.env`:

```bash
# Основные настройки Flask
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# База данных PostgreSQL
DATABASE_URL=postgresql://vip_user:your_secure_password@localhost:5432/vip_applications

# Telegram настройки
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Email конфигурация
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com

# Админ учетные данные (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# PostgreSQL пароль
POSTGRES_PASSWORD=your_secure_postgres_password
```

## 🚀 Развертывание

### Автоматическое развертывание
```bash
chmod +x deploy.sh
./deploy.sh
```

### Ручное развертывание
```bash
# Создание директорий
mkdir -p logs/nginx app/static/uploads docker/ssl

# Сборка и запуск
docker-compose -f docker/docker-compose.production.yml up -d --build
```

## 🔒 Настройка безопасности

### 1. SSL сертификаты
```bash
# Создание самоподписанного сертификата (для тестирования)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/ssl/key.pem \
    -out docker/ssl/cert.pem

# Для продакшена используйте Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### 2. Настройка файрвола
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 3. Настройка Nginx с SSL
Раскомментируйте HTTPS секцию в `docker/nginx.conf` и обновите домен.

## 📊 Мониторинг и логирование

### Проверка статуса
```bash
# Статус контейнеров
docker-compose -f docker/docker-compose.production.yml ps

# Логи приложения
docker-compose -f docker/docker-compose.production.yml logs -f web

# Логи Nginx
docker-compose -f docker/docker-compose.production.yml logs -f nginx
```

### Health check
```bash
curl http://localhost/health
```

### Мониторинг ресурсов
```bash
# Использование ресурсов
docker stats

# Дисковое пространство
df -h

# Память
free -h
```

## 🔄 Обновление приложения

### 1. Остановка текущей версии
```bash
docker-compose -f docker/docker-compose.production.yml down
```

### 2. Обновление кода
```bash
git pull origin main
```

### 3. Пересборка и запуск
```bash
docker-compose -f docker/docker-compose.production.yml up -d --build
```

## 💾 Резервное копирование

### Создание бэкапа
```bash
# Бэкап базы данных
docker exec vip_postgres pg_dump -U vip_user vip_applications > backup_$(date +%Y%m%d_%H%M%S).sql

# Бэкап загруженных файлов
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz app/static/uploads/
```

### Восстановление из бэкапа
```bash
# Восстановление базы данных
docker exec -i vip_postgres psql -U vip_user vip_applications < backup_file.sql

# Восстановление файлов
tar -xzf uploads_backup_file.tar.gz
```

## 🛠️ Устранение неполадок

### Проблемы с подключением к базе данных
```bash
# Проверка подключения
docker exec vip_postgres psql -U vip_user -d vip_applications -c "SELECT 1;"

# Перезапуск PostgreSQL
docker-compose -f docker/docker-compose.production.yml restart postgres
```

### Проблемы с Redis
```bash
# Проверка Redis
docker exec vip_redis redis-cli ping

# Перезапуск Redis
docker-compose -f docker/docker-compose.production.yml restart redis
```

### Проблемы с приложением
```bash
# Проверка логов
docker-compose -f docker/docker-compose.production.yml logs web

# Перезапуск приложения
docker-compose -f docker/docker-compose.production.yml restart web
```

### Проблемы с Nginx
```bash
# Проверка конфигурации
docker exec vip_nginx nginx -t

# Перезапуск Nginx
docker-compose -f docker/docker-compose.production.yml restart nginx
```

## 📈 Оптимизация производительности

### Настройка Gunicorn
Отредактируйте `gunicorn.conf.py`:
```python
# Увеличьте количество воркеров для высоких нагрузок
workers = multiprocessing.cpu_count() * 2 + 1

# Настройте таймауты
timeout = 60
keepalive = 5
```

### Настройка Nginx
В `docker/nginx.conf`:
```nginx
# Увеличьте буферы для больших файлов
client_max_body_size 32M;
proxy_buffer_size 128k;
proxy_buffers 4 256k;
```

### Настройка PostgreSQL
```sql
-- Увеличьте shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Настройте work_mem
ALTER SYSTEM SET work_mem = '4MB';

-- Перезапустите PostgreSQL
SELECT pg_reload_conf();
```

## 🔐 Дополнительные меры безопасности

### 1. Регулярные обновления
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose -f docker/docker-compose.production.yml pull
```

### 2. Мониторинг безопасности
```bash
# Проверка уязвимостей в образах
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image vip-main-web:production
```

### 3. Настройка fail2ban
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs`
2. Проверьте статус сервисов: `docker-compose ps`
3. Проверьте health check: `curl localhost/health`
4. Обратитесь к документации или создайте issue в репозитории