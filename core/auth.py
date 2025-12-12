"""Модуль аутентификации и работы с пользователями"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'data' / 'users.db'


def get_db():
    """Получить соединение с БД"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация БД"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            birth_date TEXT,
            birth_time TEXT,
            birth_city TEXT,
            birth_lat REAL,
            birth_lon REAL,
            gender TEXT DEFAULT 'male',
            is_premium INTEGER DEFAULT 0,
            premium_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            calc_type TEXT NOT NULL,
            calc_date TEXT NOT NULL,
            calc_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Хэширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(email: str, password: str, name: str = None) -> Optional[int]:
    """Создать пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
            (email.lower(), hash_password(password), name)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def authenticate(email: str, password: str) -> Optional[Dict]:
    """Аутентификация пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT * FROM users WHERE email = ? AND password_hash = ?',
        (email.lower(), hash_password(password))
    )
    user = cursor.fetchone()
    
    if user:
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (datetime.now().isoformat(), user['id'])
        )
        conn.commit()
        conn.close()
        return dict(user)
    
    conn.close()
    return None


def create_session(user_id: int) -> str:
    """Создать сессию"""
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=30)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)',
        (user_id, token, expires.isoformat())
    )
    conn.commit()
    conn.close()
    
    return token


def get_user_by_token(token: str) -> Optional[Dict]:
    """Получить пользователя по токену"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.* FROM users u
        JOIN sessions s ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ?
    ''', (token, datetime.now().isoformat()))
    
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None


def update_profile(user_id: int, data: Dict) -> bool:
    """Обновить профиль пользователя"""
    conn = get_db()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key in ['name', 'birth_date', 'birth_time', 'birth_city', 'birth_lat', 'birth_lon', 'gender']:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if fields:
        values.append(user_id)
        cursor.execute(f'UPDATE users SET {", ".join(fields)} WHERE id = ?', values)
        conn.commit()
    
    conn.close()
    return True


def delete_session(token: str):
    """Удалить сессию"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()


def save_calculation(user_id: int, calc_type: str, calc_date: str, calc_data: str):
    """Сохранить расчёт"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO calculations (user_id, calc_type, calc_date, calc_data) VALUES (?, ?, ?, ?)',
        (user_id, calc_type, calc_date, calc_data)
    )
    conn.commit()
    conn.close()


def get_user_calculations(user_id: int, limit: int = 10):
    """Получить историю расчётов"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM calculations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    )
    calcs = cursor.fetchall()
    conn.close()
    return [dict(c) for c in calcs]


# Инициализация БД при импорте
init_db()
