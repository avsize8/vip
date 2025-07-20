#!/usr/bin/env python3
"""
Скрипт для миграции данных из SQLite в PostgreSQL
Использование: python migrate_db.py
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_sqlite_connection():
    """Подключение к SQLite базе данных"""
    sqlite_path = os.getenv('SQLITE_DATABASE', 'instance/applications.db')
    if not os.path.exists(sqlite_path):
        print(f"SQLite база данных не найдена: {sqlite_path}")
        return None
    
    return sqlite3.connect(sqlite_path)

def get_postgres_connection():
    """Подключение к PostgreSQL базе данных"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL не установлена в переменных окружения")
        return None
    
    try:
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        return None

def create_postgres_tables(conn):
    """Создание таблиц в PostgreSQL"""
    cursor = conn.cursor()
    
    # Создание таблицы заявок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(100),
            service_type VARCHAR(100),
            message TEXT,
            ip_address VARCHAR(45),
            status VARCHAR(20) DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Создание таблицы статей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            excerpt TEXT,
            is_featured BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Создание таблицы команды
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            position VARCHAR(100),
            bio TEXT,
            photo_url VARCHAR(200),
            is_active BOOLEAN DEFAULT TRUE,
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Создание таблицы услуг
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            icon VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("Таблицы в PostgreSQL созданы успешно")

def migrate_data(sqlite_conn, postgres_conn):
    """Миграция данных из SQLite в PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Миграция заявок
    print("Миграция заявок...")
    sqlite_cursor.execute("SELECT * FROM applications")
    applications = sqlite_cursor.fetchall()
    
    for app in applications:
        postgres_cursor.execute("""
            INSERT INTO applications (id, name, phone, email, service_type, message, ip_address, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, app)
    
    # Миграция статей
    print("Миграция статей...")
    sqlite_cursor.execute("SELECT * FROM articles")
    articles = sqlite_cursor.fetchall()
    
    for article in articles:
        postgres_cursor.execute("""
            INSERT INTO articles (id, title, slug, content, excerpt, is_featured, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, article)
    
    # Миграция команды
    print("Миграция команды...")
    sqlite_cursor.execute("SELECT * FROM team_members")
    team_members = sqlite_cursor.fetchall()
    
    for member in team_members:
        postgres_cursor.execute("""
            INSERT INTO team_members (id, name, position, bio, photo_url, is_active, order_index, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, member)
    
    # Миграция услуг
    print("Миграция услуг...")
    sqlite_cursor.execute("SELECT * FROM services")
    services = sqlite_cursor.fetchall()
    
    for service in services:
        postgres_cursor.execute("""
            INSERT INTO services (id, name, description, icon, is_active, order_index, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, service)
    
    postgres_conn.commit()
    print("Миграция данных завершена успешно")

def main():
    """Основная функция"""
    print("Начинаем миграцию данных из SQLite в PostgreSQL...")
    
    # Подключение к базам данных
    sqlite_conn = get_sqlite_connection()
    if not sqlite_conn:
        sys.exit(1)
    
    postgres_conn = get_postgres_connection()
    if not postgres_conn:
        sqlite_conn.close()
        sys.exit(1)
    
    try:
        # Создание таблиц в PostgreSQL
        create_postgres_tables(postgres_conn)
        
        # Миграция данных
        migrate_data(sqlite_conn, postgres_conn)
        
        print("Миграция завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка во время миграции: {e}")
        postgres_conn.rollback()
        sys.exit(1)
    
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    main() 