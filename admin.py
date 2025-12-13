"""
Админка для управления текстами интерпретаций натальной карты.
Расширенная версия с поддержкой:
- Планеты в знаках и домах (объединённый раздел с разделением по полу)
- Аспекты
- Стихии (с разбивкой по знакам и полу)
- Планеты (описания отдельных планет)
- Дома (отдельно)
- Градусы (1-30 для каждого знака)
- Королевские и разрушительные градусы
- Состояние планет (обитель/экзальтация/изгнание/падение)

Запуск: python admin.py
Доступ: http://localhost:8080/admin
"""

import json
from config import ADMIN_USER, ADMIN_PASS, ADMIN_PORT
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Конфигурация
BASE_DIR = Path(__file__).parent
TEXTS_DIR = BASE_DIR / "data" / "texts"
TEXTS_FILE = BASE_DIR / "data" / "texts.json"  # legacy
# ADMIN_USER из config.py
# ADMIN_PASS из config.py
SESSION_SECRET = secrets.token_hex(32)

app = FastAPI(title="Админка Натальной Карты")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Названия планет и знаков для отображения
PLANET_NAMES = {
    "Sun": "☉ Солнце",
    "Moon": "☾ Луна", 
    "Mercury": "☿ Меркурий",
    "Venus": "♀ Венера",
    "Mars": "♂ Марс",
    "Jupiter": "♃ Юпитер",
    "Saturn": "♄ Сатурн",
    "Uranus": "♅ Уран",
    "Neptune": "♆ Нептун",
    "Pluto": "♇ Плутон",
    "Lilith": "⚸ Лилит",
    "North_node": "☊ Сев. узел",
    "South_node": "☋ Юж. узел"
}

PLANET_KEYS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Lilith", "North_node", "South_node"]

SIGN_NAMES = {
    "Ari": "♈ Овен",
    "Tau": "♉ Телец",
    "Gem": "♊ Близнецы",
    "Cnc": "♋ Рак",
    "Leo": "♌ Лев",
    "Vir": "♍ Дева",
    "Lib": "♎ Весы",
    "Sco": "♏ Скорпион",
    "Sag": "♐ Стрелец",
    "Cap": "♑ Козерог",
    "Aqu": "♒ Водолей",
    "Pis": "♓ Рыбы"
}

SIGN_KEYS = ["Ari", "Tau", "Gem", "Cnc", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]

SIGN_NAMES_RU = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнецы", "Cnc": "Рак",
    "Leo": "Лев", "Vir": "Дева", "Lib": "Весы", "Sco": "Скорпион",
    "Sag": "Стрелец", "Cap": "Козерог", "Aqu": "Водолей", "Pis": "Рыбы"
}

HOUSE_NAMES = {str(i): f"{i} дом" for i in range(1, 13)}

ASPECT_NAMES = {
    "Соединение": "☌ Соединение",
    "Секстиль": "✶ Секстиль",
    "Квадрат": "□ Квадрат",
    "Тригон": "△ Тригон",
    "Оппозиция": "☍ Оппозиция"
}

# Стихии с их знаками
ELEMENTS = {
    "fire": {"name": "🔥 Огонь", "signs": ["Ari", "Leo", "Sag"]},
    "earth": {"name": "🌍 Земля", "signs": ["Tau", "Vir", "Cap"]},
    "air": {"name": "💨 Воздух", "signs": ["Gem", "Lib", "Aqu"]},
    "water": {"name": "💧 Вода", "signs": ["Cnc", "Sco", "Pis"]}
}

DIGNITY_NAMES = {
    "domicile": "🏠 Обитель",
    "exaltation": "⬆️ Экзальтация",
    "detriment": "⬇️ Изгнание",
    "fall": "📉 Падение"
}


def get_current_user(request: Request) -> Optional[str]:
    return request.session.get("user")

def require_auth(request: Request) -> str:
    user = get_current_user(request)
    if not user:
        return None
    return user


def load_texts() -> dict:
    """Загружает тексты из разбитых JSON файлов"""
    texts = {'signs': {}, 'houses': {}, 'aspects': {}}
    
    # Загружаем из новых файлов
    signs_file = TEXTS_DIR / 'planets_in_signs.json'
    houses_file = TEXTS_DIR / 'planets_in_houses.json'
    aspects_file = TEXTS_DIR / 'aspects.json'
    
    if signs_file.exists():
        with open(signs_file, 'r', encoding='utf-8') as f:
            texts['signs'] = json.load(f)
    
    if houses_file.exists():
        with open(houses_file, 'r', encoding='utf-8') as f:
            texts['houses'] = json.load(f)
    
    if aspects_file.exists():
        with open(aspects_file, 'r', encoding='utf-8') as f:
            texts['aspects'] = json.load(f)
    
    return texts



def count_texts_stats():
    texts = load_texts()
    stats = {}
    signs_filled = sum(1 for k,v in texts.get('signs',{}).items() if isinstance(v,dict) for g in ['general','male','female'] if v.get(g) and len(str(v.get(g,'')))>10)
    stats['signs'] = {'filled': signs_filled, 'total': 468}
    houses_filled = sum(1 for k,v in texts.get('houses',{}).items() if isinstance(v,dict) for g in ['general','male','female'] if v.get(g) and len(str(v.get(g,'')))>10)
    stats['houses'] = {'filled': houses_filled, 'total': 468}
    aspects_filled = sum(1 for p,v in texts.get('aspects',{}).items() if isinstance(v,dict) for t,txt in v.items() if txt and len(str(txt))>10)
    stats['aspects'] = {'filled': aspects_filled, 'total': 630}
    return stats

def save_texts(data: dict):
    """Сохраняет тексты в разбитые JSON файлы"""
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if 'signs' in data:
        with open(TEXTS_DIR / 'planets_in_signs.json', 'w', encoding='utf-8') as f:
            json.dump(data['signs'], f, ensure_ascii=False, indent=2)
    
    if 'houses' in data:
        with open(TEXTS_DIR / 'planets_in_houses.json', 'w', encoding='utf-8') as f:
            json.dump(data['houses'], f, ensure_ascii=False, indent=2)
    
    if 'aspects' in data:
        with open(TEXTS_DIR / 'aspects.json', 'w', encoding='utf-8') as f:
            json.dump(data['aspects'], f, ensure_ascii=False, indent=2)


# === Общие стили ===
COMMON_STYLES = """
:root { 
    --pico-primary: #bf5af2;
    --pico-background-color: #000;
    --pico-card-background-color: rgba(29, 29, 31, 0.8);
    --pico-muted-color: #86868b;
    --pico-secondary: #5e5ce6;
}
body { 
    background: #000; 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}
.container { max-width: 1200px; padding: 20px; }
h1, h2, h3 { color: #bf5af2; }
.back-link { color: #bf5af2; display: inline-block; margin-bottom: 20px; }
.nav-tabs { display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }
.tab-btn { padding: 10px 15px; background: rgba(29, 29, 31, 0.8); color: white; text-decoration: none; border-radius: 8px; font-size: 14px; }
.tab-btn:hover, .tab-btn.active { background: #bf5af2; }
.text-block { background: rgba(29, 29, 31, 0.8); padding: 15px; border-radius: 10px; margin: 15px 0; }
.text-block.empty { border-left: 4px solid #ff5252; }
.text-block.filled { border-left: 4px solid #4caf50; }
.text-block label { color: #bf5af2; font-weight: bold; display: block; margin-bottom: 10px; }
textarea { width: 100%; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); color: white; padding: 10px; border-radius: 5px; min-height: 100px; }
button { margin-top: 10px; }
.generate-btn { background: #4caf50; padding: 8px 15px; font-size: 14px; margin-left: 10px; }
.gender-tabs { display: flex; gap: 5px; margin-bottom: 10px; }
.gender-tab { padding: 5px 10px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); color: #888; cursor: pointer; border-radius: 4px; font-size: 12px; }
.gender-tab.active { background: #bf5af2; color: white; border-color: #bf5af2; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
.stat-card { background: rgba(29, 29, 31, 0.8); padding: 15px; border-radius: 10px; text-align: center; }
.stat-card h4 { color: #bf5af2; margin: 0 0 10px 0; font-size: 14px; }
.stat-filled { color: #4caf50; font-size: 20px; font-weight: bold; }
.stat-empty { color: #ff5252; font-size: 20px; font-weight: bold; }
.nav-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
.nav-card { background: rgba(29, 29, 31, 0.8); padding: 20px; border-radius: 10px; text-decoration: none; color: white; transition: transform 0.2s; }
.nav-card:hover { transform: translateY(-3px); background: rgba(255,255,255,0.05); }
.nav-card h3 { color: #bf5af2; margin: 0 0 8px 0; font-size: 16px; }
.nav-card p { color: #888; margin: 0; font-size: 13px; }
.section-title { border-bottom: 2px solid #bf5af2; padding-bottom: 10px; margin: 30px 0 20px 0; }
.combo-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
.small-textarea { min-height: 60px; }
"""


# === Страница логина ===
@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    error = request.query_params.get("error")
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Вход - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container" style="max-width: 500px; margin-top: 100px;">
            <article style="background: rgba(29, 29, 31, 0.8); padding: 30px; border-radius: 15px;">
                <hgroup>
                    <h1 style="text-align: center;">🔐 Вход в админку</h1>
                    <h2 style="text-align: center; color: #888;">Натальная Карта</h2>
                </hgroup>
                {'<p style="color: #ff5252; text-align: center;">' + error + '</p>' if error else ''}
                <form method="POST" action="/admin/login">
                    <input type="text" name="username" placeholder="Логин" required autofocus style="background: rgba(0,0,0,0.4); border-color: rgba(255,255,255,0.1);">
                    <input type="password" name="password" placeholder="Пароль" required style="background: rgba(0,0,0,0.4); border-color: rgba(255,255,255,0.1);">
                    <button type="submit" style="width: 100%;">Войти</button>
                </form>
            </article>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/admin", status_code=303)
    return RedirectResponse(url="/admin/login?error=Неверный логин или пароль", status_code=303)


@app.get("/admin/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


# === Главная страница админки ===
@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админка - Натальная Карта</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1>🌌 Админка Натальной Карты</h1>
                <a href="/admin/logout" style="color: #bf5af2;">Выйти ({user}) →</a>
            </div>
            
            <h2 class="section-title">📁 Основные разделы</h2>
            <div class="nav-grid">
                <a href="/admin/planet-sign-house" class="nav-card">
                    <h3>🪐 Планеты в знаках и домах</h3>
                    <p>Солнце в Овне в 1 доме (муж/жен)</p>
                </a>
                <a href="/admin/aspects" class="nav-card">
                    <h3>⭐ Аспекты</h3>
                    <p>Солнце тригон Луна, Марс квадрат Сатурн...</p>
                </a>
            </div>
            
            <h2 class="section-title">📚 Справочники</h2>
            <div class="nav-grid">
                <a href="/admin/elements" class="nav-card">
                    <h3>🔥 Стихии</h3>
                    <p>Огонь-Овен (муж/жен), Земля-Телец...</p>
                </a>
                <a href="/admin/planets-info" class="nav-card">
                    <h3>🪐 Планеты</h3>
                    <p>Описания планет (Солнце, Луна...)</p>
                </a>
                <a href="/admin/houses-general" class="nav-card">
                    <h3>🏛️ Дома</h3>
                    <p>12 домов отдельно</p>
                </a>
                <a href="/admin/dignities" class="nav-card">
                    <h3>👑 Достоинства планет</h3>
                    <p>Обитель, экзальтация, изгнание, падение</p>
                </a>
            </div>
            
            <h2 class="section-title">🎯 Градусы</h2>
            <div class="nav-grid">
                <a href="/admin/degrees" class="nav-card">
                    <h3>📐 Все градусы</h3>
                    <p>1-30° для каждого знака (360 градусов)</p>
                </a>
                <a href="/admin/royal-degrees" class="nav-card">
                    <h3>👑 Королевские градусы</h3>
                    <p>18° Овна, 9° Близнецов, 7° Льва...</p>
                </a>
                <a href="/admin/destructive-degrees" class="nav-card">
                    <h3>💀 Разрушительные градусы</h3>
                    <p>23° Овна, 13° Близнецов, 10° Льва...</p>
                </a>
            </div>
            
            <h2 class="section-title">🛠️ Инструменты</h2>
            <div class="nav-grid">
                <a href="/admin/generate" class="nav-card">
                    <h3>🤖 AI Генерация</h3>
                    <p>Инструкции по генерации через Cursor</p>
                </a>
                <a href="/" class="nav-card">
                    <h3>🌐 Перейти на сайт</h3>
                    <p>Открыть главную страницу</p>
                </a>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# === ОБЪЕДИНЁННЫЙ РАЗДЕЛ: Планеты в знаках и домах ===
@app.get("/admin/planet-sign-house", response_class=HTMLResponse)
async def admin_planet_sign_house(request: Request, planet: str = None, sign: str = None, gender: str = "male"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    
    # Инициализируем структуру если нет
    if "sign_house_combos" not in texts:
        texts["sign_house_combos"] = {}
    
    # Табы планет
    planets_list = "".join([
        f'<a href="/admin/planet-sign-house?planet={p}&sign={sign or "Ari"}&gender={gender}" class="tab-btn {"active" if planet == p else ""}">{PLANET_NAMES.get(p, p)}</a>'
        for p in PLANET_KEYS
    ])
    
    # Табы знаков (если выбрана планета)
    signs_list = ""
    if planet:
        signs_list = "".join([
            f'<a href="/admin/planet-sign-house?planet={planet}&sign={s}&gender={gender}" class="tab-btn {"active" if sign == s else ""}">{SIGN_NAMES.get(s, s)}</a>'
            for s in SIGN_KEYS
        ])
    
    # Табы пола
    gender_tabs = ""
    if planet and sign:
        gender_tabs = f"""
        <div class="gender-tabs" style="margin: 20px 0;">
            <a href="/admin/planet-sign-house?planet={planet}&sign={sign}&gender=male" class="tab-btn {'active' if gender == 'male' else ''}">♂️ Мужчина</a>
            <a href="/admin/planet-sign-house?planet={planet}&sign={sign}&gender=female" class="tab-btn {'active' if gender == 'female' else ''}">♀️ Женщина</a>
        </div>
        """
    
    # Форма редактирования домов
    form_html = ""
    if planet and sign:
        planet_name = PLANET_NAMES.get(planet, planet)
        sign_name = SIGN_NAMES.get(sign, sign)
        gender_name = "Мужчина" if gender == "male" else "Женщина"
        
        form_html = f"<h2>{planet_name} в {sign_name} ({gender_name})</h2>"
        form_html += '<div class="combo-grid">'
        
        # Получаем или создаём данные
        combo_data = texts.get("sign_house_combos", {}).get(planet, {}).get(sign, {}).get(gender, {})
        
        for house_num in range(1, 13):
            house_key = str(house_num)
            text = combo_data.get(house_key, "")
            is_empty = "ЗАПОЛНИТЬ" in str(text) or not text or len(text) < 10
            
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>В {house_num} доме</label>
                <textarea name="{house_key}" rows="3" class="small-textarea">{text}</textarea>
            </div>
            """
        
        form_html += '</div>'
        form_html = f'<form method="POST" action="/admin/planet-sign-house/save?planet={planet}&sign={sign}&gender={gender}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты в знаках и домах - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🪐 Планеты в знаках и домах</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <p style="color: #888;">Выберите планету → знак → пол, затем заполните тексты для каждого дома</p>
            
            <h3 style="color: #bf5af2; margin-top: 20px;">Планета:</h3>
            <div class="nav-tabs">{planets_list}</div>
            
            {'<h3 style="color: #bf5af2; margin-top: 20px;">Знак:</h3><div class="nav-tabs">' + signs_list + '</div>' if signs_list else ''}
            
            {gender_tabs}
            {form_html if form_html else '<p style="color: #888; margin-top: 30px;">Выберите планету для начала редактирования</p>'}
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/planet-sign-house/save")
async def save_planet_sign_house(request: Request, planet: str, sign: str, gender: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    # Инициализируем структуру
    if "sign_house_combos" not in texts:
        texts["sign_house_combos"] = {}
    if planet not in texts["sign_house_combos"]:
        texts["sign_house_combos"][planet] = {}
    if sign not in texts["sign_house_combos"][planet]:
        texts["sign_house_combos"][planet][sign] = {}
    if gender not in texts["sign_house_combos"][planet][sign]:
        texts["sign_house_combos"][planet][sign][gender] = {}
    
    for key, value in form.items():
        texts["sign_house_combos"][planet][sign][gender][key] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/planet-sign-house?planet={planet}&sign={sign}&gender={gender}", status_code=303)


# === Аспекты ===
@app.get("/admin/aspects", response_class=HTMLResponse)
async def admin_aspects(request: Request, pair: str = None):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    aspects_data = texts.get("aspects", {})
    
    pairs_list = "".join([
        f'<a href="/admin/aspects?pair={p}" class="tab-btn {"active" if pair == p else ""}">{p.replace("_", " — ")}</a>'
        for p in aspects_data.keys()
    ])
    
    form_html = ""
    if pair and pair in aspects_data:
        form_html = f"<h2>{pair.replace('_', ' — ')}</h2>"
        for asp, text in aspects_data[pair].items():
            is_empty = "ЗАПОЛНИТЬ" in str(text) or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{ASPECT_NAMES.get(asp, asp)}</label>
                <textarea name="{pair}_{asp}" rows="4">{text}</textarea>
            </div>
            """
        form_html = f'<form method="POST" action="/admin/aspects/save?pair={pair}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Аспекты - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>⭐ Аспекты</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="nav-tabs" style="max-height: 300px; overflow-y: auto;">{pairs_list}</div>
            {form_html if form_html else '<p style="color: #888;">Выберите пару планет для редактирования</p>'}
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/aspects/save")
async def save_aspects(request: Request, pair: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "aspects" not in texts:
        texts["aspects"] = {}
    if pair not in texts["aspects"]:
        texts["aspects"][pair] = {}
    
    prefix = f"{pair}_"
    for key, value in form.items():
        if key.startswith(prefix):
            asp = key.replace(prefix, "")
            texts["aspects"][pair][asp] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/aspects?pair={pair}", status_code=303)


# === Стихии (расширенные: Стихия × Знак × Пол) ===
@app.get("/admin/elements", response_class=HTMLResponse)
async def admin_elements(request: Request, element: str = "fire", gender: str = "male"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    
    # Инициализируем структуру если нет
    if "elements_extended" not in texts:
        texts["elements_extended"] = {}
    
    # Табы стихий
    element_tabs = "".join([
        f'<a href="/admin/elements?element={e}&gender={gender}" class="tab-btn {"active" if element == e else ""}">{ELEMENTS[e]["name"]}</a>'
        for e in ELEMENTS.keys()
    ])
    
    # Табы пола
    gender_tabs = f"""
    <div class="gender-tabs" style="margin: 20px 0;">
        <a href="/admin/elements?element={element}&gender=male" class="tab-btn {'active' if gender == 'male' else ''}">♂️ Мужчина</a>
        <a href="/admin/elements?element={element}&gender=female" class="tab-btn {'active' if gender == 'female' else ''}">♀️ Женщина</a>
    </div>
    """
    
    # Форма для знаков этой стихии
    elem_data = ELEMENTS.get(element, {})
    elem_name = elem_data.get("name", element)
    signs = elem_data.get("signs", [])
    gender_name = "Мужчина" if gender == "male" else "Женщина"
    
    form_html = f"<h2>{elem_name} — {gender_name}</h2>"
    
    elem_texts = texts.get("elements_extended", {}).get(element, {})
    
    for sign_key in signs:
        sign_name = SIGN_NAMES.get(sign_key, sign_key)
        text = elem_texts.get(sign_key, {}).get(gender, "")
        is_empty = not text or len(text) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>{elem_name} — {sign_name}</label>
            <textarea name="{sign_key}" rows="4">{text}</textarea>
        </div>
        """
    
    form_html = f'<form method="POST" action="/admin/elements/save?element={element}&gender={gender}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Стихии - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🔥 Стихии</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <p style="color: #888;">Стихия × Знак × Пол</p>
            
            <div class="nav-tabs">{element_tabs}</div>
            {gender_tabs}
            {form_html}
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/elements/save")
async def save_elements(request: Request, element: str, gender: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "elements_extended" not in texts:
        texts["elements_extended"] = {}
    if element not in texts["elements_extended"]:
        texts["elements_extended"][element] = {}
    
    for key, value in form.items():
        if key not in texts["elements_extended"][element]:
            texts["elements_extended"][element][key] = {}
        texts["elements_extended"][element][key][gender] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/elements?element={element}&gender={gender}", status_code=303)


# === Планеты (описания отдельных планет) ===
@app.get("/admin/planets-info", response_class=HTMLResponse)
async def admin_planets_info(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    planets_data = texts.get("planets_info", {})
    
    form_html = ""
    for planet_key in PLANET_KEYS:
        planet_name = PLANET_NAMES.get(planet_key, planet_key)
        text = planets_data.get(planet_key, {}).get("description", "")
        is_empty = not text or len(text) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>{planet_name}</label>
            <textarea name="{planet_key}" rows="4">{text}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🪐 Планеты</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <p style="color: #888;">Общие описания планет</p>
            
            <form method="POST" action="/admin/planets-info/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/planets-info/save")
async def save_planets_info(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "planets_info" not in texts:
        texts["planets_info"] = {}
    
    for key, value in form.items():
        texts["planets_info"][key] = {"description": value}
    
    save_texts(texts)
    return RedirectResponse(url="/admin/planets-info", status_code=303)


# === Дома (общие) ===
@app.get("/admin/houses-general", response_class=HTMLResponse)
async def admin_houses_general(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    houses_data = texts.get("houses_general", {})
    
    form_html = ""
    for i in range(1, 13):
        house_key = str(i)
        house_data = houses_data.get(house_key, {})
        desc = house_data.get('description', '') if isinstance(house_data, dict) else house_data
        is_empty = not desc or len(desc) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>{i} дом</label>
            <textarea name="{house_key}" rows="4">{desc}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Дома - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🏛️ Дома</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            <form method="POST" action="/admin/houses-general/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/houses-general/save")
async def save_houses_general(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "houses_general" not in texts:
        texts["houses_general"] = {}
    
    for key, value in form.items():
        texts["houses_general"][key] = {"description": value}
    
    save_texts(texts)
    return RedirectResponse(url="/admin/houses-general", status_code=303)


# === Достоинства планет ===
@app.get("/admin/dignities", response_class=HTMLResponse)
async def admin_dignities(request: Request, dignity: str = "domicile"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    dignities_data = texts.get("planet_dignities", {}).get(dignity, {})
    
    dignity_tabs = "".join([
        f'<a href="/admin/dignities?dignity={d}" class="tab-btn {"active" if dignity == d else ""}">{DIGNITY_NAMES.get(d, d)}</a>'
        for d in ["domicile", "exaltation", "detriment", "fall"]
    ])
    
    form_html = f"<h2>{DIGNITY_NAMES.get(dignity, dignity)}</h2>"
    for key, data in dignities_data.items():
        planet = data.get("planet", key)
        sign = data.get("sign", "")
        desc = data.get("description", "")
        is_empty = not desc or len(desc) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>{planet} в {sign}</label>
            <textarea name="{key}" rows="4">{desc}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Достоинства планет - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>👑 Достоинства планет</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="nav-tabs">{dignity_tabs}</div>
            
            <form method="POST" action="/admin/dignities/save?dignity={dignity}">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/dignities/save")
async def save_dignities(request: Request, dignity: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "planet_dignities" not in texts:
        texts["planet_dignities"] = {}
    if dignity not in texts["planet_dignities"]:
        texts["planet_dignities"][dignity] = {}
    
    for key, value in form.items():
        if key in texts["planet_dignities"][dignity]:
            texts["planet_dignities"][dignity][key]["description"] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/dignities?dignity={dignity}", status_code=303)


# === Градусы ===
@app.get("/admin/degrees", response_class=HTMLResponse)
async def admin_degrees(request: Request, sign: str = "Ari"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    degrees_data = texts.get("degrees", {}).get(sign, {})
    
    sign_tabs = "".join([
        f'<a href="/admin/degrees?sign={s}" class="tab-btn {"active" if sign == s else ""}">{SIGN_NAMES.get(s, s)}</a>'
        for s in SIGN_KEYS
    ])
    
    form_html = f"<h2>{SIGN_NAMES.get(sign, sign)}</h2>"
    for deg in range(1, 31):
        deg_key = str(deg)
        deg_data = degrees_data.get(deg_key, {})
        desc = deg_data.get("description", "") if isinstance(deg_data, dict) else deg_data
        
        form_html += f"""
        <div class="text-block" style="padding: 10px;">
            <label style="display: inline;">{deg}°</label>
            <textarea name="{deg_key}" rows="2" style="margin-top: 5px;">{desc}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Градусы - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>📐 Градусы</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="nav-tabs">{sign_tabs}</div>
            
            <form method="POST" action="/admin/degrees/save?sign={sign}">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/degrees/save")
async def save_degrees(request: Request, sign: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "degrees" not in texts:
        texts["degrees"] = {}
    if sign not in texts["degrees"]:
        texts["degrees"][sign] = {}
    
    for key, value in form.items():
        texts["degrees"][sign][key] = {"description": value}
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/degrees?sign={sign}", status_code=303)


# === Королевские градусы ===
@app.get("/admin/royal-degrees", response_class=HTMLResponse)
async def admin_royal_degrees(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    royal_data = texts.get("royal_degrees", {})
    
    form_html = ""
    for key, data in royal_data.items():
        name = data.get('name', key) if isinstance(data, dict) else key
        desc = data.get('description', '') if isinstance(data, dict) else data
        is_empty = not desc or len(desc) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>👑 {name}</label>
            <textarea name="{key}" rows="4">{desc}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Королевские градусы - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>👑 Королевские градусы</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            <p style="color: #888;">18° Овна, 9° Близнецов, 7° Льва, 25° Девы, 13° Скорпиона, 11° Козерога, 30° Водолея</p>
            <form method="POST" action="/admin/royal-degrees/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/royal-degrees/save")
async def save_royal_degrees(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "royal_degrees" not in texts:
        texts["royal_degrees"] = {}
    
    for key, value in form.items():
        if key in texts["royal_degrees"]:
            if isinstance(texts["royal_degrees"][key], dict):
                texts["royal_degrees"][key]["description"] = value
            else:
                texts["royal_degrees"][key] = {"name": key, "description": value}
    
    save_texts(texts)
    return RedirectResponse(url="/admin/royal-degrees", status_code=303)


# === Разрушительные градусы ===
@app.get("/admin/destructive-degrees", response_class=HTMLResponse)
async def admin_destructive_degrees(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    destructive_data = texts.get("destructive_degrees", {})
    
    form_html = ""
    for key, data in destructive_data.items():
        name = data.get('name', key) if isinstance(data, dict) else key
        desc = data.get('description', '') if isinstance(data, dict) else data
        is_empty = not desc or len(desc) < 10
        
        form_html += f"""
        <div class="text-block {'empty' if is_empty else 'filled'}">
            <label>💀 {name}</label>
            <textarea name="{key}" rows="4">{desc}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Разрушительные градусы - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>💀 Разрушительные градусы</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            <p style="color: #888;">23° Овна, 13° Близнецов, 10° Льва, 1° Весов, 19° Скорпиона, 19° Козерога, 4° Рыб</p>
            <form method="POST" action="/admin/destructive-degrees/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/destructive-degrees/save")
async def save_destructive_degrees(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "destructive_degrees" not in texts:
        texts["destructive_degrees"] = {}
    
    for key, value in form.items():
        if key in texts["destructive_degrees"]:
            if isinstance(texts["destructive_degrees"][key], dict):
                texts["destructive_degrees"][key]["description"] = value
            else:
                texts["destructive_degrees"][key] = {"name": key, "description": value}
    
    save_texts(texts)
    return RedirectResponse(url="/admin/destructive-degrees", status_code=303)


# === Страница AI генерации ===
@app.get("/admin/generate", response_class=HTMLResponse)
async def admin_generate_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Генерация - Админка</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}
        .info-box {{ background: rgba(29, 29, 31, 0.8); padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .warning {{ background: #ff525233; border-left: 4px solid #ff5252; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        code {{ background: rgba(0,0,0,0.4); padding: 2px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <main class="container">
            <h1>🤖 AI Генерация текстов</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="warning">
                <strong>⚠️ Важно!</strong><br>
                Генерация текстов происходит через Cursor AI или GPT API.
            </div>
            
            <div class="info-box">
                <h3 style="color: #4caf50;">Как это работает:</h3>
                <ol>
                    <li>Откройте проект в Cursor IDE</li>
                    <li>Попросите Claude/GPT сгенерировать тексты</li>
                    <li>AI обновит файл <code>texts.json</code></li>
                    <li>Изменения сразу появятся в админке</li>
                </ol>
            </div>
            
            <div class="info-box">
                <h3 style="color: #bf5af2;">Примеры промптов:</h3>
                <p><strong>Для планет в знаках и домах:</strong></p>
                <textarea rows="4" style="width:100%; background:rgba(0,0,0,0.4); color:white;">Заполни texts.json раздел sign_house_combos: для Солнца в Овне в каждом доме (1-12) напиши 2-3 предложения. Отдельно для мужчин и женщин.</textarea>
                
                <p style="margin-top: 15px;"><strong>Для стихий:</strong></p>
                <textarea rows="4" style="width:100%; background:rgba(0,0,0,0.4); color:white;">Заполни texts.json раздел elements_extended: для стихии Огонь напиши описания для Овна, Льва, Стрельца. Отдельно для мужчин и женщин.</textarea>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# === API для генерации (заглушка) ===
@app.post("/admin/api/generate")
async def api_generate_text(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    data = await request.json()
    gen_type = data.get("type")
    
    return {"text": "[AI] Используйте Cursor IDE или GPT API для генерации.", "status": "stub"}


if __name__ == "__main__":
    print("🌌 Запуск админки Натальной Карты")
    print(f"📍 Адрес: http://localhost:8080/admin")
    print(f"🔐 Логин: {ADMIN_USER}")
    print(f"🔐 Пароль: {ADMIN_PASS}")
    uvicorn.run(app, host="0.0.0.0", port=ADMIN_PORT)
