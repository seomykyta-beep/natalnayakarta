"""
Админка для управления текстами интерпретаций натальной карты.
Расширенная версия с поддержкой:
- Планеты в знаках (с разделением по полу)
- Планеты в домах (с разделением по полу)
- Аспекты
- Стихии
- Знаки зодиака (отдельно)
- Дома (отдельно)
- Градусы (1-30 для каждого знака)
- Королевские и разрушительные градусы
- Состояние планет (обитель/экзальтация/изгнание/падение)

Запуск: python admin.py
Доступ: http://localhost:8080/admin
"""

import json
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
TEXTS_FILE = BASE_DIR / "texts.json"
ADMIN_USER = "admin"
ADMIN_PASS = "astro2025"
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

ELEMENT_NAMES = {
    "fire": "🔥 Огонь",
    "earth": "🌍 Земля",
    "air": "💨 Воздух",
    "water": "💧 Вода"
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
    if TEXTS_FILE.exists():
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_texts(data: dict):
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# === Общие стили ===
COMMON_STYLES = """
:root { --pico-primary: #e94560; }
body { background: #1a1a2e; }
.container { max-width: 1200px; padding: 20px; }
h1, h2, h3 { color: #ffd700; }
.back-link { color: #e94560; display: inline-block; margin-bottom: 20px; }
.nav-tabs { display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }
.tab-btn { padding: 10px 15px; background: #16213e; color: white; text-decoration: none; border-radius: 8px; font-size: 14px; }
.tab-btn:hover, .tab-btn.active { background: #e94560; }
.text-block { background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; }
.text-block.empty { border-left: 4px solid #ff5252; }
.text-block.filled { border-left: 4px solid #4caf50; }
.text-block label { color: #ffd700; font-weight: bold; display: block; margin-bottom: 10px; }
textarea { width: 100%; background: #0f1424; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px; min-height: 100px; }
button { margin-top: 10px; }
.generate-btn { background: #4caf50; padding: 8px 15px; font-size: 14px; margin-left: 10px; }
.gender-tabs { display: flex; gap: 5px; margin-bottom: 10px; }
.gender-tab { padding: 5px 10px; background: #0f1424; border: 1px solid #333; color: #888; cursor: pointer; border-radius: 4px; font-size: 12px; }
.gender-tab.active { background: #e94560; color: white; border-color: #e94560; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
.stat-card { background: #16213e; padding: 15px; border-radius: 10px; text-align: center; }
.stat-card h4 { color: #ffd700; margin: 0 0 10px 0; font-size: 14px; }
.stat-filled { color: #4caf50; font-size: 20px; font-weight: bold; }
.stat-empty { color: #ff5252; font-size: 20px; font-weight: bold; }
.nav-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
.nav-card { background: #16213e; padding: 20px; border-radius: 10px; text-decoration: none; color: white; transition: transform 0.2s; }
.nav-card:hover { transform: translateY(-3px); background: #1f2b4a; }
.nav-card h3 { color: #ffd700; margin: 0 0 8px 0; font-size: 16px; }
.nav-card p { color: #888; margin: 0; font-size: 13px; }
.section-title { border-bottom: 2px solid #e94560; padding-bottom: 10px; margin: 30px 0 20px 0; }
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
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container" style="max-width: 500px; margin-top: 100px;">
            <article style="background: #16213e; padding: 30px; border-radius: 15px;">
                <hgroup>
                    <h1 style="text-align: center;">🔐 Вход в админку</h1>
                    <h2 style="text-align: center; color: #888;">Натальная Карта</h2>
                </hgroup>
                {'<p style="color: #ff5252; text-align: center;">' + error + '</p>' if error else ''}
                <form method="POST" action="/admin/login">
                    <input type="text" name="username" placeholder="Логин" required autofocus style="background: #0f1424; border-color: #333;">
                    <input type="password" name="password" placeholder="Пароль" required style="background: #0f1424; border-color: #333;">
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
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1>🌌 Админка Натальной Карты</h1>
                <a href="/admin/logout" style="color: #e94560;">Выйти ({user}) →</a>
            </div>
            
            <h2 class="section-title">📁 Основные разделы</h2>
            <div class="nav-grid">
                <a href="/admin/signs" class="nav-card">
                    <h3>🪐 Планеты в знаках</h3>
                    <p>Солнце в Овне, Луна в Тельце... (с разделением по полу)</p>
                </a>
                <a href="/admin/houses" class="nav-card">
                    <h3>🏠 Планеты в домах</h3>
                    <p>Солнце в 1 доме, Луна во 2 доме... (с разделением по полу)</p>
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
                    <p>Огонь, Земля, Воздух, Вода</p>
                </a>
                <a href="/admin/zodiac" class="nav-card">
                    <h3>♈ Знаки зодиака</h3>
                    <p>12 знаков отдельно</p>
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


# === Планеты в знаках (с разделением по полу) ===
@app.get("/admin/signs", response_class=HTMLResponse)
async def admin_signs(request: Request, planet: str = None, gender: str = "general"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    signs_data = texts.get("signs", {})
    
    planets_list = "".join([
        f'<a href="/admin/signs?planet={p}&gender={gender}" class="tab-btn {"active" if planet == p else ""}">{PLANET_NAMES.get(p, p)}</a>'
        for p in signs_data.keys()
    ])
    
    gender_tabs = f"""
    <div class="gender-tabs" style="margin: 20px 0;">
        <a href="/admin/signs?planet={planet}&gender=general" class="tab-btn {'active' if gender == 'general' else ''}">👤 Общее</a>
        <a href="/admin/signs?planet={planet}&gender=male" class="tab-btn {'active' if gender == 'male' else ''}">♂️ Мужчина</a>
        <a href="/admin/signs?planet={planet}&gender=female" class="tab-btn {'active' if gender == 'female' else ''}">♀️ Женщина</a>
    </div>
    """ if planet else ""
    
    form_html = ""
    if planet and planet in signs_data:
        form_html = f"<h2>{PLANET_NAMES.get(planet, planet)} в знаках ({gender})</h2>"
        for sign, text_data in signs_data[planet].items():
            # Получаем текст в зависимости от структуры
            if isinstance(text_data, dict):
                text = text_data.get(gender, text_data.get("general", ""))
            else:
                text = text_data if gender == "general" else ""
            
            is_empty = "ЗАПОЛНИТЬ" in str(text) or "ДОПОЛНИТЬ" in str(text) or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{SIGN_NAMES.get(sign, sign)}</label>
                <textarea name="{planet}_{sign}_{gender}" rows="4">{text}</textarea>
                <button type="button" onclick="generateText('{planet}', '{sign}', '{gender}', this)" class="generate-btn">🤖 Сгенерировать</button>
            </div>
            """
        form_html = f'<form method="POST" action="/admin/signs/save?planet={planet}&gender={gender}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты в знаках - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🪐 Планеты в знаках</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="nav-tabs">{planets_list}</div>
            {gender_tabs}
            {form_html if form_html else '<p style="color: #888;">Выберите планету для редактирования</p>'}
        </main>
        
        <script>
        async function generateText(planet, sign, gender, btn) {{
            btn.innerHTML = '⏳...';
            btn.disabled = true;
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'sign', planet, sign, gender}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) btn.parentElement.querySelector('textarea').value = data.text;
            }} catch(e) {{ alert('Ошибка: ' + e.message); }}
            btn.innerHTML = '🤖 Сгенерировать';
            btn.disabled = false;
        }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/signs/save")
async def save_signs(request: Request, planet: str, gender: str = "general"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if planet not in texts.get("signs", {}):
        texts["signs"][planet] = {}
    
    for key, value in form.items():
        parts = key.split("_")
        if len(parts) >= 3 and parts[0] == planet:
            sign = parts[1]
            g = parts[2]
            
            if sign not in texts["signs"][planet]:
                texts["signs"][planet][sign] = {"general": "", "male": "", "female": ""}
            
            if isinstance(texts["signs"][planet][sign], str):
                old_text = texts["signs"][planet][sign]
                texts["signs"][planet][sign] = {"general": old_text, "male": "", "female": ""}
            
            texts["signs"][planet][sign][g] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/signs?planet={planet}&gender={gender}", status_code=303)


# === Планеты в домах (с разделением по полу) ===
@app.get("/admin/houses", response_class=HTMLResponse)
async def admin_houses(request: Request, planet: str = None, gender: str = "general"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    houses_data = texts.get("houses", {})
    
    planets_list = "".join([
        f'<a href="/admin/houses?planet={p}&gender={gender}" class="tab-btn {"active" if planet == p else ""}">{PLANET_NAMES.get(p, p)}</a>'
        for p in houses_data.keys()
    ])
    
    gender_tabs = f"""
    <div class="gender-tabs" style="margin: 20px 0;">
        <a href="/admin/houses?planet={planet}&gender=general" class="tab-btn {'active' if gender == 'general' else ''}">👤 Общее</a>
        <a href="/admin/houses?planet={planet}&gender=male" class="tab-btn {'active' if gender == 'male' else ''}">♂️ Мужчина</a>
        <a href="/admin/houses?planet={planet}&gender=female" class="tab-btn {'active' if gender == 'female' else ''}">♀️ Женщина</a>
    </div>
    """ if planet else ""
    
    form_html = ""
    if planet and planet in houses_data:
        form_html = f"<h2>{PLANET_NAMES.get(planet, planet)} в домах ({gender})</h2>"
        for house in [str(i) for i in range(1, 13)]:
            text_data = houses_data[planet].get(house, {})
            if isinstance(text_data, dict):
                text = text_data.get(gender, text_data.get("general", ""))
            else:
                text = text_data if gender == "general" else ""
            
            is_empty = "ЗАПОЛНИТЬ" in str(text) or "ДОПОЛНИТЬ" in str(text) or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{HOUSE_NAMES.get(house, house)}</label>
                <textarea name="{planet}_{house}_{gender}" rows="4">{text}</textarea>
                <button type="button" onclick="generateText('{planet}', '{house}', '{gender}', this)" class="generate-btn">🤖 Сгенерировать</button>
            </div>
            """
        form_html = f'<form method="POST" action="/admin/houses/save?planet={planet}&gender={gender}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты в домах - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🏠 Планеты в домах</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="nav-tabs">{planets_list}</div>
            {gender_tabs}
            {form_html if form_html else '<p style="color: #888;">Выберите планету для редактирования</p>'}
        </main>
        
        <script>
        async function generateText(planet, house, gender, btn) {{
            btn.innerHTML = '⏳...';
            btn.disabled = true;
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'house', planet, house, gender}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) btn.parentElement.querySelector('textarea').value = data.text;
            }} catch(e) {{ alert('Ошибка: ' + e.message); }}
            btn.innerHTML = '🤖 Сгенерировать';
            btn.disabled = false;
        }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/houses/save")
async def save_houses(request: Request, planet: str, gender: str = "general"):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if planet not in texts.get("houses", {}):
        texts["houses"][planet] = {}
    
    for key, value in form.items():
        parts = key.split("_")
        if len(parts) >= 3 and parts[0] == planet:
            house = parts[1]
            g = parts[2]
            
            if house not in texts["houses"][planet]:
                texts["houses"][planet][house] = {"general": "", "male": "", "female": ""}
            
            if isinstance(texts["houses"][planet][house], str):
                old_text = texts["houses"][planet][house]
                texts["houses"][planet][house] = {"general": old_text, "male": "", "female": ""}
            
            texts["houses"][planet][house][g] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/houses?planet={planet}&gender={gender}", status_code=303)


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
                <button type="button" onclick="generateAspect('{pair}', '{asp}', this)" class="generate-btn">🤖 Сгенерировать</button>
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
        
        <script>
        async function generateAspect(pair, aspect, btn) {{
            btn.innerHTML = '⏳...';
            btn.disabled = true;
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'aspect', pair, aspect}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) btn.parentElement.querySelector('textarea').value = data.text;
            }} catch(e) {{ alert('Ошибка: ' + e.message); }}
            btn.innerHTML = '🤖 Сгенерировать';
            btn.disabled = false;
        }}
        </script>
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


# === Стихии ===
@app.get("/admin/elements", response_class=HTMLResponse)
async def admin_elements(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    elements_data = texts.get("elements", {})
    
    form_html = ""
    for elem_key, elem_data in elements_data.items():
        elem_name = ELEMENT_NAMES.get(elem_key, elem_key)
        signs = ", ".join([SIGN_NAMES_RU.get(s, s) for s in elem_data.get("signs", [])])
        
        form_html += f"""
        <div class="text-block">
            <label>{elem_name} ({signs})</label>
            <p style="color: #888; font-size: 12px;">Общее описание:</p>
            <textarea name="{elem_key}_description" rows="3">{elem_data.get('description', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для мужчины:</p>
            <textarea name="{elem_key}_description_male" rows="3">{elem_data.get('description_male', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для женщины:</p>
            <textarea name="{elem_key}_description_female" rows="3">{elem_data.get('description_female', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Стихии - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>🔥 Стихии</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            <form method="POST" action="/admin/elements/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/elements/save")
async def save_elements(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    for key, value in form.items():
        parts = key.split("_", 1)
        if len(parts) == 2:
            elem_key, field = parts
            if elem_key in texts.get("elements", {}):
                texts["elements"][elem_key][field] = value
    
    save_texts(texts)
    return RedirectResponse(url="/admin/elements", status_code=303)


# === Знаки зодиака ===
@app.get("/admin/zodiac", response_class=HTMLResponse)
async def admin_zodiac(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    zodiac_data = texts.get("zodiac_signs", {})
    
    form_html = ""
    for sign_key in ["Ari", "Tau", "Gem", "Cnc", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]:
        sign_data = zodiac_data.get(sign_key, {})
        sign_name = SIGN_NAMES.get(sign_key, sign_key)
        
        form_html += f"""
        <div class="text-block">
            <label>{sign_name}</label>
            <p style="color: #888; font-size: 12px;">Общее описание:</p>
            <textarea name="{sign_key}_description" rows="3">{sign_data.get('description', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для мужчины:</p>
            <textarea name="{sign_key}_description_male" rows="3">{sign_data.get('description_male', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для женщины:</p>
            <textarea name="{sign_key}_description_female" rows="3">{sign_data.get('description_female', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Знаки зодиака - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}</style>
    </head>
    <body>
        <main class="container">
            <h1>♈ Знаки зодиака</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            <form method="POST" action="/admin/zodiac/save">
                {form_html}
                <button type="submit">💾 Сохранить все</button>
            </form>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/zodiac/save")
async def save_zodiac(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if "zodiac_signs" not in texts:
        texts["zodiac_signs"] = {}
    
    for key, value in form.items():
        parts = key.split("_", 1)
        if len(parts) == 2:
            sign_key, field = parts
            if sign_key not in texts["zodiac_signs"]:
                texts["zodiac_signs"][sign_key] = {"name": SIGN_NAMES_RU.get(sign_key, sign_key)}
            texts["zodiac_signs"][sign_key][field] = value
    
    save_texts(texts)
    return RedirectResponse(url="/admin/zodiac", status_code=303)


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
        
        form_html += f"""
        <div class="text-block">
            <label>{i} дом</label>
            <p style="color: #888; font-size: 12px;">Общее описание:</p>
            <textarea name="{house_key}_description" rows="3">{house_data.get('description', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для мужчины:</p>
            <textarea name="{house_key}_description_male" rows="3">{house_data.get('description_male', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для женщины:</p>
            <textarea name="{house_key}_description_female" rows="3">{house_data.get('description_female', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Дома - Админка</title>
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
        parts = key.split("_", 1)
        if len(parts) == 2:
            house_key, field = parts
            if house_key not in texts["houses_general"]:
                texts["houses_general"][house_key] = {"name": f"{house_key} дом"}
            texts["houses_general"][house_key][field] = value
    
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
        planet = data.get("planet", "")
        sign = data.get("sign", "")
        
        form_html += f"""
        <div class="text-block">
            <label>{planet} в {sign}</label>
            <p style="color: #888; font-size: 12px;">Общее описание:</p>
            <textarea name="{key}_description" rows="3">{data.get('description', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для мужчины:</p>
            <textarea name="{key}_description_male" rows="3">{data.get('description_male', '')}</textarea>
            <p style="color: #888; font-size: 12px; margin-top: 10px;">Для женщины:</p>
            <textarea name="{key}_description_female" rows="3">{data.get('description_female', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Достоинства планет - Админка</title>
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
        parts = key.rsplit("_", 1)
        if len(parts) == 2:
            item_key, field = parts
            if item_key in texts["planet_dignities"][dignity]:
                texts["planet_dignities"][dignity][item_key][field] = value
    
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
        for s in ["Ari", "Tau", "Gem", "Cnc", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
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
        form_html += f"""
        <div class="text-block">
            <label>👑 {data.get('name', key)}</label>
            <textarea name="{key}" rows="4">{data.get('description', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Королевские градусы - Админка</title>
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
    
    for key, value in form.items():
        if key in texts.get("royal_degrees", {}):
            texts["royal_degrees"][key]["description"] = value
    
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
        form_html += f"""
        <div class="text-block">
            <label>💀 {data.get('name', key)}</label>
            <textarea name="{key}" rows="4">{data.get('description', '')}</textarea>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Разрушительные градусы - Админка</title>
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
    
    for key, value in form.items():
        if key in texts.get("destructive_degrees", {}):
            texts["destructive_degrees"][key]["description"] = value
    
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
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>{COMMON_STYLES}
        .info-box {{ background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .warning {{ background: #ff525233; border-left: 4px solid #ff5252; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        code {{ background: #0f1424; padding: 2px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <main class="container">
            <h1>🤖 AI Генерация текстов</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="warning">
                <strong>⚠️ Важно!</strong><br>
                Генерация текстов происходит через Cursor AI. Кнопки "Сгенерировать" работают как заглушки.
                Для реальной генерации используйте Cursor IDE.
            </div>
            
            <div class="info-box">
                <h3 style="color: #4caf50;">Как это работает:</h3>
                <ol>
                    <li>Откройте проект в Cursor IDE</li>
                    <li>Попросите Claude сгенерировать тексты</li>
                    <li>Claude обновит файл <code>texts.json</code></li>
                    <li>Изменения сразу появятся в админке</li>
                </ol>
            </div>
            
            <div class="info-box">
                <h3 style="color: #ffd700;">Примеры промптов:</h3>
                <p><strong>Для планет в знаках:</strong></p>
                <textarea rows="4" style="width:100%; background:#0f1424; color:white;">Заполни texts.json: для Солнца в каждом знаке напиши 3-5 предложений. Добавь версии для мужчин и женщин. Стиль: профессиональный астрологический.</textarea>
                
                <p style="margin-top: 15px;"><strong>Для градусов:</strong></p>
                <textarea rows="4" style="width:100%; background:#0f1424; color:white;">Заполни texts.json: для каждого градуса Овна (1-30) напиши краткое описание его значения по Сабианским символам.</textarea>
            </div>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# === API для генерации ===
@app.post("/admin/api/generate")
async def api_generate_text(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    data = await request.json()
    gen_type = data.get("type")
    
    if gen_type == "test":
        return {"status": "ok", "message": "API работает"}
    
    # Заглушки для генерации
    if gen_type == "sign":
        planet = data.get("planet", "")
        sign = data.get("sign", "")
        gender = data.get("gender", "general")
        planet_name = PLANET_NAMES.get(planet, planet)
        sign_name = SIGN_NAMES.get(sign, sign)
        gender_text = {"general": "", "male": " (мужчина)", "female": " (женщина)"}.get(gender, "")
        return {"text": f"[AI] {planet_name} в {sign_name}{gender_text}: Используйте Cursor IDE для генерации."}
    
    if gen_type == "house":
        planet = data.get("planet", "")
        house = data.get("house", "")
        gender = data.get("gender", "general")
        planet_name = PLANET_NAMES.get(planet, planet)
        gender_text = {"general": "", "male": " (мужчина)", "female": " (женщина)"}.get(gender, "")
        return {"text": f"[AI] {planet_name} в {house} доме{gender_text}: Используйте Cursor IDE для генерации."}
    
    if gen_type == "aspect":
        pair = data.get("pair", "")
        aspect = data.get("aspect", "")
        return {"text": f"[AI] {pair} ({aspect}): Используйте Cursor IDE для генерации."}
    
    return {"text": "", "error": "Неизвестный тип"}


if __name__ == "__main__":
    print("🌌 Запуск админки Натальной Карты")
    print(f"📍 Адрес: http://localhost:8080/admin")
    print(f"🔐 Логин: {ADMIN_USER}")
    print(f"🔐 Пароль: {ADMIN_PASS}")
    uvicorn.run(app, host="0.0.0.0", port=8080)
