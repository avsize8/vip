#!/usr/bin/env python3
"""
Скрипт запуска приложения
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Настройка окружения"""
    # Создание необходимых директорий
    directories = ['logs', 'instance', 'app/static/uploads']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def check_basic_requirements():
    """Базовая проверка требований"""
    # Проверка Python версии
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Проверка .env файла
    if not os.path.exists('.env'):
        print("⚠️  Файл .env не найден. Создайте его на основе env.example")
        return False
    
    return True

def start_application():
    """Запуск приложения"""
    try:
        from app import create_app
        app = create_app()
        
        print("🚀 Приложение запущено на http://localhost:5000")
        print("📊 Админ-панель: http://localhost:5000/admin")
        print("🔧 API: http://localhost:5000/api/v1/health")
        print("\nНажмите Ctrl+C для остановки")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

def main():
    """Основная функция"""
    # Тихая настройка
    setup_environment()
    
    # Базовая проверка
    if not check_basic_requirements():
        print("Создайте файл .env и попробуйте снова")
        sys.exit(1)
    
    # Запуск
    start_application()

if __name__ == '__main__':
    main() 