# Многоэтапная сборка для оптимизации размера образа
FROM python:3.12.9-slim as builder

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.12.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копирование виртуального окружения
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Установка рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/logs /app/instance /app/app/static/uploads && \
    chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Переменные окружения
ENV PYTHONPATH=/app
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production

# Проверка здоровья приложения
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Порт
EXPOSE 5000

# Команда запуска с Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]