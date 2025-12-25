"""PostgreSQL database connection for user management"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DB_CONFIG = {
    'host': 'localhost',
    'database': 'natal_users',
    'user': 'natal_user',
    'password': 'NatalChart2024!'
}

@contextmanager
def get_connection():
    """Get database connection with context manager"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()

@contextmanager
def get_cursor():
    """Get database cursor with auto-commit"""
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute query and optionally fetch results"""
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        if fetch_one:
            row = cursor.fetchone() if cursor.description else None; return dict(row) if row else None
        if fetch_all:
            return [dict(row) for row in cursor.fetchall()] if cursor.description else []
        return cursor.rowcount

def test_connection():
    """Test database connection"""
    try:
        with get_cursor() as cursor:
            cursor.execute('SELECT 1')
            return True
    except Exception as e:
        print(f'Database connection error: {e}')
        return False
