#!/usr/bin/env python3
"""
Скрипт для хеширования паролей админа
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.helpers import SecurityHelper

def hash_password():
    """Хеширование пароля"""
    if len(sys.argv) != 2:
        print("Использование: python hash_password.py <password>")
        print("Пример: python hash_password.py mypassword123")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = SecurityHelper.hash_password(password)
    
    print(f"Пароль: {password}")
    print(f"Хеш: {hashed}")
    print("\nДобавьте хеш в .env файл:")
    print(f"ADMIN_PASSWORD={hashed}")

if __name__ == '__main__':
    hash_password() 