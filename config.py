"""Конфигурация приложения из .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

# Telegram Bot
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Admin Panel
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'admin123')

# Server
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
ADMIN_PORT = int(os.getenv('ADMIN_PORT', 8080))

# Paths
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
CHARTS_DIR = Path(os.getenv('CHARTS_DIR', BASE_DIR / 'charts'))
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', BASE_DIR / 'reports'))
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

# Создаём папки если не существуют
for d in [DATA_DIR, CHARTS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Sentry (optional monitoring)
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Initialize Sentry if DSN provided
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
    except ImportError:
        pass
