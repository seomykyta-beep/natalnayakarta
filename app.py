"""Основное веб-приложение натальной карты"""
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.gzip import GZipMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from pydantic import BaseModel
from typing import Optional
import logging

from config import BOT_TOKEN, HOST, PORT, CHARTS_DIR, REPORTS_DIR, TEMPLATES_DIR, STATIC_DIR
from pathlib import Path
DATA_DIR = Path("/opt/natal_chart/data_cache")
from engine import calculate_chart_with_mode, generate_pdf
from core.auth import register_user, login_user, get_user_by_id, update_user_profile, decode_token, save_calculation, get_user_calculations
from core.database import test_connection
from core.synastry import calculate_synastry

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI
app = FastAPI(title='Натальная Карта', version='2.0')

# Telegram Bot
dp = Dispatcher()
bot = None
if BOT_TOKEN:
    try:
        bot = Bot(token=BOT_TOKEN)
        logger.info('Telegram bot initialized')
    except Exception as e:
        logger.error(f'Failed to init bot: {e}')

# Templates & Static
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount('/charts', StaticFiles(directory=str(CHARTS_DIR)), name='charts')
app.mount('/reports', StaticFiles(directory=str(REPORTS_DIR)), name='reports')
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')


class UserData(BaseModel):
    """Входные данные для расчёта карты"""
    name: str
    gender: Optional[str] = 'male'
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    
    # Режим: natal / solar / lunar
    mode: Optional[str] = 'natal'
    
    # Транзиты
    transit_year: Optional[int] = None
    transit_month: Optional[int] = None
    transit_day: Optional[int] = None
    transit_hour: Optional[int] = None
    transit_minute: Optional[int] = None
    transit_city: Optional[str] = None
    transit_lat: Optional[float] = None
    transit_lon: Optional[float] = None
    
    # Соляр
    solar_year: Optional[int] = None
    solar_city: Optional[str] = None
    solar_lat: Optional[float] = None
    solar_lon: Optional[float] = None
    
    # Лунар
    lunar_year: Optional[int] = None
    lunar_month: Optional[int] = None
    lunar_city: Optional[str] = None
    lunar_lat: Optional[float] = None
    lunar_lon: Optional[float] = None
    
    # Орбисы
    orb_conjunction: Optional[int] = None
    orb_sextile: Optional[int] = None
    orb_square: Optional[int] = None
    orb_trine: Optional[int] = None
    orb_quincunx: Optional[int] = None
    orb_opposition: Optional[int] = None




# ============ AUTH ENDPOINTS ============

class RegisterData(BaseModel):
    phone: str
    password: str
    name: Optional[str] = None

class LoginData(BaseModel):
    phone: str
    password: str

class ProfileUpdateData(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    current_city: Optional[str] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    email: Optional[str] = None
    telegram: Optional[str] = None

def get_current_user(request: Request):
    """Get current user from token"""
    token = request.cookies.get('auth_token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return get_user_by_id(payload['user_id'])

@app.post('/api/auth/register')
async def api_register(data: RegisterData):
    """Register new user"""
    result = register_user(data.phone, data.password, data.name)
    if result['success']:
        from fastapi.responses import JSONResponse
        response = JSONResponse({'success': True, 'user_id': result['user_id']})
        response.set_cookie('auth_token', result['token'], httponly=True, max_age=7*24*3600, samesite='lax')
        return response
    return {'success': False, 'error': result['error']}

@app.post('/api/auth/login')
async def api_login(data: LoginData):
    """Login user"""
    result = login_user(data.phone, data.password)
    if result['success']:
        from fastapi.responses import JSONResponse
        response = JSONResponse({'success': True, 'user_id': result['user_id'], 'name': result['name']})
        response.set_cookie('auth_token', result['token'], httponly=True, max_age=7*24*3600, samesite='lax')
        return response
    return {'success': False, 'error': result['error']}

@app.post('/api/auth/logout')
async def api_logout():
    """Logout user"""
    from fastapi.responses import JSONResponse
    response = JSONResponse({'success': True})
    response.delete_cookie('auth_token')
    return response

@app.get('/api/auth/me')
async def api_get_me(request: Request):
    """Get current user info"""
    user = get_current_user(request)
    if not user:
        return {'authenticated': False}
    return {'authenticated': True, 'user': user}

@app.get('/api/user/profile')
async def api_get_profile(request: Request):
    """Get user profile"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    return {'success': True, 'profile': user}

@app.put('/api/user/profile')
async def api_update_profile(request: Request, data: ProfileUpdateData):
    """Update user profile"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = update_user_profile(user['id'], update_data)
    return result

@app.get('/api/user/calculations')
async def api_get_calculations(request: Request):
    """Get user calculation history"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    
    calculations = get_user_calculations(user['id'])
    return {'success': True, 'calculations': calculations}


class SynastryData(BaseModel):
    """Данные для расчёта синастрии"""
    # Первый человек
    name1: str
    year1: int
    month1: int
    day1: int
    hour1: int
    minute1: int
    city1: str
    lat1: Optional[float] = None
    lon1: Optional[float] = None
    gender1: Optional[str] = 'male'
    
    # Второй человек
    name2: str
    year2: int
    month2: int
    day2: int
    hour2: int
    minute2: int
    city2: str
    lat2: Optional[float] = None
    lon2: Optional[float] = None
    gender2: Optional[str] = 'female'

@app.get('/')
async def landing(request: Request):
    """Landing page"""
    return templates.TemplateResponse('landing.html', {'request': request})


@app.get('/app')
async def home(request: Request):
    """Приложение"""
    response = templates.TemplateResponse('index.html', {'request': request}); response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'; response.headers['Pragma'] = 'no-cache'; return response






@app.get('/profile')
async def profile_page(request: Request):
    """Страница профиля"""
    return templates.TemplateResponse('profile.html', {'request': request})




@app.get('/login')
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse('login.html', {'request': request})

@app.get('/register')
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse('register.html', {'request': request})

@app.get('/auth')
async def auth_page(request: Request):
    """Страница авторизации"""
    return templates.TemplateResponse('auth.html', {'request': request})


class LoginData(BaseModel):
    email: str
    password: str


class RegisterData(BaseModel):
    name: str
    email: str
    password: str


@app.post('/api/auth/register')
async def api_register(data: RegisterData):
    """Регистрация"""
    if len(data.password) < 6:
        return {'success': False, 'error': 'Пароль минимум 6 символов'}
    
    user_id = create_user(data.email, data.password, data.name)
    if user_id:
        return {'success': True}
    return {'success': False, 'error': 'Email уже занят'}


@app.post('/api/auth/login')
async def api_login(data: LoginData):
    """Вход"""
    user = authenticate(data.email, data.password)
    if user:
        token = create_session(user['id'])
        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'is_premium': bool(user['is_premium']),
                'birth_date': user['birth_date'],
                'birth_time': user['birth_time'],
                'birth_city': user['birth_city'],
                'gender': user['gender']
            }
        }
    return {'success': False, 'error': 'Неверный email или пароль'}




class ProfileData(BaseModel):
    token: str
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    gender: Optional[str] = None


@app.post('/api/profile/update')
async def api_update_profile(data: ProfileData):
    """Обновление профиля"""
    user = get_user_by_token(data.token)
    if not user:
        return {'success': False, 'error': 'Не авторизован'}
    
    profile_data = {
        'name': data.name,
        'birth_date': data.birth_date,
        'birth_time': data.birth_time,
        'birth_city': data.birth_city,
        'birth_lat': data.birth_lat,
        'birth_lon': data.birth_lon,
        'gender': data.gender
    }
    # Убираем None значения
    profile_data = {k: v for k, v in profile_data.items() if v is not None}
    
    update_profile(user['id'], profile_data)
    return {'success': True}


@app.get('/api/profile')
async def api_get_profile(token: str):
    """Получение профиля"""
    user = get_user_by_token(token)
    if not user:
        return {'success': False, 'error': 'Не авторизован'}
    
    return {
        'success': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'is_premium': bool(user['is_premium']),
            'birth_date': user['birth_date'],
            'birth_time': user['birth_time'],
            'birth_city': user['birth_city'],
            'birth_lat': user['birth_lat'],
            'birth_lon': user['birth_lon'],
            'gender': user['gender']
        }
    }


@app.post('/api/auth/logout')
async def api_logout(token: str):
    """Выход"""
    delete_session(token)
    return {'success': True}


@app.post('/api/calculate')
async def api_calculate(data: UserData):
    """API расчёта натальной карты"""
    logger.info(f'Calculate request: {data.name}, mode={data.mode}')
    
    # Собираем орбисы
    custom_orbs = {}
    orb_mapping = {
        0: data.orb_conjunction,
        60: data.orb_sextile,
        90: data.orb_square,
        120: data.orb_trine,
        150: data.orb_quincunx,
        180: data.orb_opposition
    }
    for angle, value in orb_mapping.items():
        if value is not None:
            custom_orbs[angle] = value
    
    result = calculate_chart_with_mode(
        name=data.name,
        year=data.year,
        month=data.month,
        day=data.day,
        hour=data.hour,
        minute=data.minute,
        city=data.city,
        lat=data.lat,
        lon=data.lon,
        gender=data.gender,
        mode=data.mode or 'natal',
        transit_year=data.transit_year,
        transit_month=data.transit_month,
        transit_day=data.transit_day,
        transit_hour=data.transit_hour,
        transit_minute=data.transit_minute,
        transit_city=data.transit_city,
        transit_lat=data.transit_lat,
        transit_lon=data.transit_lon,
        solar_year=data.solar_year,
        solar_city=data.solar_city,
        solar_lat=data.solar_lat,
        solar_lon=data.solar_lon,
        lunar_year=data.lunar_year,
        lunar_month=data.lunar_month,
        lunar_city=data.lunar_city,
        lunar_lat=data.lunar_lat,
        lunar_lon=data.lunar_lon,
        custom_orbs=custom_orbs if custom_orbs else None
    )
    
    result['gender'] = data.gender
    generate_pdf(result)
    # Save calculation data for later PDF generation
    safe_name = ''.join(c for c in result.get('name', 'unknown') if c.isalnum() or c in ' _-')[:50]
    data_file = DATA_DIR / f'{safe_name}.json'
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, default=str)
    
    logger.info(f'Calculate complete: {data.name}')
    return result


@app.get('/api/pdf')
async def get_pdf(name: str, mode: str = 'full'):
    """Скачать PDF отчёт по режиму"""
    from core.pdf import generate_pdf_by_mode
    
    safe_name = ''.join(c for c in name if c.isalnum() or c in ' _-')[:50]
    
    # Load saved calculation data
    data_file = DATA_DIR / f'{safe_name}.json'
    if not data_file.exists():
        # Fallback to existing report
        file_path = REPORTS_DIR / f'report_{safe_name}.pdf'
        if file_path.exists():
            return FileResponse(str(file_path), filename=f'Horoscope_{safe_name}.pdf')
        return {'error': 'Data not found'}
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Generate PDF for specific mode
    suffix = '' if mode == 'full' else f'_{mode}'
    pdf_path = generate_pdf_by_mode(data, mode)
    
    if pdf_path and Path(pdf_path).exists():
        mode_labels = {'full': '', 'natal': '_Натал', 'transit': '_Транзиты', 'solar': '_Соляр', 'lunar': '_Лунар', 'synastry': '_Синастрия'}
        filename = f'Horoscope_{safe_name}{mode_labels.get(mode, "")}.pdf'
        return FileResponse(str(pdf_path), filename=filename)
    
    return {'error': 'PDF generation failed'}


# ============ AUTH ENDPOINTS ============

class RegisterData(BaseModel):
    phone: str
    password: str
    name: Optional[str] = None

class LoginData(BaseModel):
    phone: str
    password: str

class ProfileUpdateData(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None
    birth_lat: Optional[float] = None
    birth_lon: Optional[float] = None
    current_city: Optional[str] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    email: Optional[str] = None
    telegram: Optional[str] = None

def get_current_user(request: Request):
    """Get current user from token"""
    token = request.cookies.get('auth_token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return get_user_by_id(payload['user_id'])

@app.post('/api/auth/register')
async def api_register(data: RegisterData):
    """Register new user"""
    result = register_user(data.phone, data.password, data.name)
    if result['success']:
        from fastapi.responses import JSONResponse
        response = JSONResponse({'success': True, 'user_id': result['user_id']})
        response.set_cookie('auth_token', result['token'], httponly=True, max_age=7*24*3600, samesite='lax')
        return response
    return {'success': False, 'error': result['error']}

@app.post('/api/auth/login')
async def api_login(data: LoginData):
    """Login user"""
    result = login_user(data.phone, data.password)
    if result['success']:
        from fastapi.responses import JSONResponse
        response = JSONResponse({'success': True, 'user_id': result['user_id'], 'name': result['name']})
        response.set_cookie('auth_token', result['token'], httponly=True, max_age=7*24*3600, samesite='lax')
        return response
    return {'success': False, 'error': result['error']}

@app.post('/api/auth/logout')
async def api_logout():
    """Logout user"""
    from fastapi.responses import JSONResponse
    response = JSONResponse({'success': True})
    response.delete_cookie('auth_token')
    return response

@app.get('/api/auth/me')
async def api_get_me(request: Request):
    """Get current user info"""
    user = get_current_user(request)
    if not user:
        return {'authenticated': False}
    return {'authenticated': True, 'user': user}

@app.get('/api/user/profile')
async def api_get_profile(request: Request):
    """Get user profile"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    return {'success': True, 'profile': user}

@app.put('/api/user/profile')
async def api_update_profile(request: Request, data: ProfileUpdateData):
    """Update user profile"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    result = update_user_profile(user['id'], update_data)
    return result

@app.get('/api/user/calculations')
async def api_get_calculations(request: Request):
    """Get user calculation history"""
    user = get_current_user(request)
    if not user:
        return {'success': False, 'error': 'Not authenticated'}
    
    calculations = get_user_calculations(user['id'])
    return {'success': True, 'calculations': calculations}


class SynastryData(BaseModel):
    name1: str
    year1: int
    month1: int
    day1: int
    hour1: int = 12
    minute1: int = 0
    city1: str = ''
    lat1: float = 55.75
    lon1: float = 37.62
    gender1: str = 'M'
    name2: str
    year2: int
    month2: int
    day2: int
    hour2: int = 12
    minute2: int = 0
    city2: str = ''
    lat2: float = 55.75
    lon2: float = 37.62


@app.post('/api/synastry')
async def api_synastry(data: SynastryData):
    """API расчёта синастрии"""
    logger.info(f'Synastry request: {data.name1} + {data.name2}')
    
    # Рассчитываем карты обоих партнёров
    chart1 = calculate_chart_with_mode(
        name=data.name1, year=data.year1, month=data.month1, day=data.day1,
        hour=data.hour1, minute=data.minute1, city=data.city1,
        lat=data.lat1, lon=data.lon1, gender=data.gender1, mode='natal'
    )
    
    chart2 = calculate_chart_with_mode(
        name=data.name2, year=data.year2, month=data.month2, day=data.day2,
        hour=data.hour2, minute=data.minute2, city=data.city2,
        lat=data.lat2, lon=data.lon2, gender='M', mode='natal'
    )
    
    # Рассчитываем синастрию
    result = calculate_synastry(chart1, chart2)
    result['name1'] = data.name1
    result['name2'] = data.name2
    
    logger.info(f'Synastry complete: {data.name1} + {data.name2}, score={result.get("score")}')
    return result



# Telegram Bot handlers
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    kb = [[types.InlineKeyboardButton(
        text='✨ Открыть гороскоп',
        web_app=types.WebAppInfo(url=f'http://{HOST}:{PORT}')
    )]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer('Нажми кнопку ниже:', reply_markup=keyboard)


async def start_bot():
    if bot:
        logger.info('Starting Telegram bot...')
        await dp.start_polling(bot)


async def start_server():
    logger.info(f'Starting server on {HOST}:{PORT}')
    config = uvicorn.Config(app=app, host=HOST, port=PORT, log_level='info')
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(start_server(), start_bot())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutting down...')
