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

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/calculate")
async def api_calculate(data: UserData):
    # Передаем координаты, если они есть
    result = calculate_real_chart(
        data.name, data.year, data.month, data.day,
        data.hour, data.minute, data.city,
        lat=data.lat, lon=data.lon,
        transit_year=data.transit_year,
        transit_month=data.transit_month,
        transit_day=data.transit_day,
        transit_hour=data.transit_hour,
        transit_minute=data.transit_minute
    )
    
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
