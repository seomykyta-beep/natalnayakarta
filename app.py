import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from pydantic import BaseModel
from engine import calculate_real_chart, generate_pdf
import os
from typing import Optional

# --- СОЗДАНИЕ ПАПОК ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

for d in [CHARTS_DIR, REPORTS_DIR, TEMPLATES_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "8538039134:AAHHT_DjPFXtW-bCaI-Sv8DS4MPAqKKSs9E" 
app = FastAPI()
dp = Dispatcher()

# Bot init
bot = None
if BOT_TOKEN != "ВАШ_ТОКЕН":
    try:
        bot = Bot(token=BOT_TOKEN)
    except: pass

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

class UserData(BaseModel):
    name: str
    gender: Optional[str] = "male"  # male / female
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    transit_year: Optional[int] = None
    transit_month: Optional[int] = None
    transit_day: Optional[int] = None
    transit_hour: Optional[int] = None
    transit_minute: Optional[int] = None
    # Настраиваемые орбисы
    orb_conjunction: Optional[int] = None
    orb_sextile: Optional[int] = None
    orb_square: Optional[int] = None
    orb_trine: Optional[int] = None
    orb_quincunx: Optional[int] = None
    orb_opposition: Optional[int] = None

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/calculate")
async def api_calculate(data: UserData):
    # Собираем пользовательские орбисы, если заданы
    custom_orbs = {}
    if data.orb_conjunction is not None:
        custom_orbs[0] = data.orb_conjunction
    if data.orb_sextile is not None:
        custom_orbs[60] = data.orb_sextile
    if data.orb_square is not None:
        custom_orbs[90] = data.orb_square
    if data.orb_trine is not None:
        custom_orbs[120] = data.orb_trine
    if data.orb_quincunx is not None:
        custom_orbs[150] = data.orb_quincunx
    if data.orb_opposition is not None:
        custom_orbs[180] = data.orb_opposition
    
    # Передаем координаты и орбисы
    result = calculate_real_chart(
        data.name, data.year, data.month, data.day,
        data.hour, data.minute, data.city,
        lat=data.lat, lon=data.lon,
        transit_year=data.transit_year,
        transit_month=data.transit_month,
        transit_day=data.transit_day,
        transit_hour=data.transit_hour,
        transit_minute=data.transit_minute,
        custom_orbs=custom_orbs if custom_orbs else None,
        gender=data.gender
    )
    
    # Добавляем gender в результат для PDF
    result['gender'] = data.gender
    generate_pdf(result)
    return result

@app.get("/api/pdf")
async def get_pdf(name: str):
    file_path = os.path.join(REPORTS_DIR, f"report_{name}.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=f"Horoscope_{name}.pdf")
    return {"error": "File not found"}

# --- TELEGRAM BOT ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.InlineKeyboardButton(text="✨ Открыть гороскоп", web_app=types.WebAppInfo(url="http://127.0.0.1:8000"))]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer("Нажми кнопку ниже:", reply_markup=keyboard)

async def start_bot():
    if bot: await dp.start_polling(bot)

async def start_server():
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(start_server(), start_bot())

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
