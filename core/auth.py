"""Authentication module for user management"""
import bcrypt
import jwt
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .database import execute_query

# JWT settings
JWT_SECRET = 'natal_chart_secret_key_2024_change_in_production'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +7XXXXXXXXXX format"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    if not digits.startswith('7'):
        digits = '7' + digits
    return '+' + digits

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    normalized = normalize_phone(phone)
    return len(normalized) == 12 and normalized.startswith('+7')

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: int) -> str:
    """Create JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def register_user(phone: str, password: str, name: str = None) -> Dict[str, Any]:
    """Register new user"""
    phone = normalize_phone(phone)
    
    if not validate_phone(phone):
        return {'success': False, 'error': 'Неверный формат телефона'}
    
    if len(password) < 6:
        return {'success': False, 'error': 'Пароль должен быть минимум 6 символов'}
    
    # Check if user exists
    existing = execute_query(
        'SELECT id FROM users WHERE phone = %s',
        (phone,), fetch_one=True
    )
    if existing:
        return {'success': False, 'error': 'Пользователь с таким номером уже существует'}
    
    # Create user
    password_hash = hash_password(password)
    result = execute_query(
        '''INSERT INTO users (phone, password_hash, name, created_at) 
           VALUES (%s, %s, %s, %s) RETURNING id''',
        (phone, password_hash, name, datetime.now()),
        fetch_one=True
    )
    
    if result:
        token = create_token(result['id'])
        return {'success': True, 'user_id': result['id'], 'token': token}
    
    return {'success': False, 'error': 'Ошибка при создании пользователя'}

def login_user(phone: str, password: str) -> Dict[str, Any]:
    """Login user"""
    phone = normalize_phone(phone)
    
    user = execute_query(
        'SELECT id, password_hash, name FROM users WHERE phone = %s',
        (phone,), fetch_one=True
    )
    
    if not user:
        return {'success': False, 'error': 'Пользователь не найден'}
    
    if not verify_password(password, user['password_hash']):
        return {'success': False, 'error': 'Неверный пароль'}
    
    # Update last login
    execute_query(
        'UPDATE users SET last_login = %s WHERE id = %s',
        (datetime.now(), user['id'])
    )
    
    token = create_token(user['id'])
    return {'success': True, 'user_id': user['id'], 'name': user['name'], 'token': token}

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return execute_query(
        '''SELECT id, phone, name, birth_date, birth_time, birth_city,
                  birth_lat, birth_lon, current_city, current_lat, current_lon,
                  email, telegram, created_at, last_login
           FROM users WHERE id = %s''',
        (user_id,), fetch_one=True
    )

def update_user_profile(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile"""
    allowed_fields = [
        'name', 'birth_date', 'birth_time', 'birth_city',
        'birth_lat', 'birth_lon', 'current_city', 'current_lat', 'current_lon',
        'email', 'telegram'
    ]
    
    updates = []
    values = []
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = %s')
            values.append(data[field])
    
    if not updates:
        return {'success': False, 'error': 'Нет данных для обновления'}
    
    values.append(user_id)
    query = f'UPDATE users SET {", ".join(updates)} WHERE id = %s'
    
    execute_query(query, tuple(values))
    return {'success': True}

def save_calculation(user_id: int, calc_type: str, input_data: dict, result_data: dict = None, pdf_path: str = None):
    """Save calculation to history"""
    import json
    execute_query(
        '''INSERT INTO calculations (user_id, calc_type, input_data, result_data, pdf_path, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (user_id, calc_type, json.dumps(input_data), json.dumps(result_data) if result_data else None, pdf_path, datetime.now())
    )

def get_user_calculations(user_id: int, limit: int = 50) -> list:
    """Get user calculation history"""
    return execute_query(
        '''SELECT id, calc_type, input_data, created_at, pdf_path
           FROM calculations WHERE user_id = %s
           ORDER BY created_at DESC LIMIT %s''',
        (user_id, limit), fetch_all=True
    )
