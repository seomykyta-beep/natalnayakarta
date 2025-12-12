"""Основное веб-приложение натальной карты"""
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from pydantic import BaseModel
from typing import Optional
import logging

from config import BOT_TOKEN, HOST, PORT, CHARTS_DIR, REPORTS_DIR, TEMPLATES_DIR, STATIC_DIR
from engine import calculate_chart_with_mode, generate_pdf
from core.auth import create_user, authenticate, create_session, get_user_by_token, update_profile, delete_session

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


@app.get('/')
async def landing(request: Request):
    """Landing page"""
    return templates.TemplateResponse('landing.html', {'request': request})


@app.get('/app')
async def home(request: Request):
    """Приложение"""
    return templates.TemplateResponse('index.html', {'request': request})






@app.get('/profile')
async def profile_page(request: Request):
    """Страница профиля"""
    return templates.TemplateResponse('profile.html', {'request': request})


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
    
    logger.info(f'Calculate complete: {data.name}')
    return result


@app.get('/api/pdf')
async def get_pdf(name: str):
    """Скачать PDF отчёт"""
    file_path = REPORTS_DIR / f'report_{name}.pdf'
    if file_path.exists():
        return FileResponse(str(file_path), filename=f'Horoscope_{name}.pdf')
    return {'error': 'File not found'}


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
