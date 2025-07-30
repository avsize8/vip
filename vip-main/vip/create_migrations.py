#!/usr/bin/env python3
"""
Скрипт для инициализации миграций базы данных
"""
import os
import sys
from app import create_app, db
from flask_migrate import init, migrate, upgrade

def init_migrations():
    """Инициализация миграций"""
    app = create_app()
    
    with app.app_context():
        # Инициализируем миграции если папка не существует
        if not os.path.exists('migrations'):
            init()
            print("✅ Миграции инициализированы")
        
        # Создаем первую миграцию
        migrate(message='Initial migration')
        print("✅ Первая миграция создана")
        
        # Применяем миграции
        upgrade()
        print("✅ Миграции применены")

if __name__ == '__main__':
    init_migrations() 