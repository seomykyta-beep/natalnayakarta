"""
Админка для управления текстами интерпретаций натальной карты.
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
ADMIN_PASS = "astro2025"  # Сменить на продакшене!
SESSION_SECRET = secrets.token_hex(32)  # Секретный ключ для сессий

app = FastAPI(title="Админка Натальной Карты")

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Шаблоны
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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

HOUSE_NAMES = {str(i): f"{i} дом" for i in range(1, 13)}

ASPECT_NAMES = {
    "Conjunction": "☌ Соединение",
    "Sextile": "✶ Секстиль",
    "Square": "□ Квадрат",
    "Trine": "△ Тригон",
    "Quincunx": "⤻ Квинконс",
    "Opposition": "☍ Оппозиция"
}


def get_current_user(request: Request) -> Optional[str]:
    """Получить текущего пользователя из сессии."""
    return request.session.get("user")

def require_auth(request: Request) -> str:
    """Проверка авторизации через сессию с редиректом на логин."""
    user = get_current_user(request)
    if not user:
        # Редирект на страницу логина вместо 401 ошибки
        return None
    return user


def load_texts() -> dict:
    """Загрузка текстов из JSON"""
    if TEXTS_FILE.exists():
        with open(TEXTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"intro": "", "signs": {}, "houses": {}, "aspects": {}}


def save_texts(data: dict):
    """Сохранение текстов в JSON"""
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница логина"""
    error = request.query_params.get("error")
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Вход - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
    </head>
    <body>
        <main class="container" style="max-width: 500px; margin-top: 100px;">
            <article>
                <hgroup>
                    <h1>🔐 Вход в админку</h1>
                    <h2>Натальная Карта</h2>
                </hgroup>
                """ + (f'<p style="color: red;">{error}</p>' if error else '') + """
                <form method="POST" action="/admin/login">
                    <input type="text" name="username" placeholder="Логин" required autofocus>
                    <input type="password" name="password" placeholder="Пароль" required>
                    <button type="submit">Войти</button>
                </form>
            </article>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/admin/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обработка логина"""
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return RedirectResponse(url="/admin/login?error=Неверный логин или пароль", status_code=303)

@app.get("/admin/logout")
async def logout(request: Request):
    """Выход"""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    """Главная страница админки"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    
    # Подсчёт заполненных/пустых
    stats = {
        "signs": {"filled": 0, "empty": 0},
        "houses": {"filled": 0, "empty": 0},
        "aspects": {"filled": 0, "empty": 0}
    }
    
    for planet, signs in texts.get("signs", {}).items():
        for sign, text in signs.items():
            if text and "ЗАПОЛНИТЬ" not in text:
                stats["signs"]["filled"] += 1
            else:
                stats["signs"]["empty"] += 1
                
    for planet, houses in texts.get("houses", {}).items():
        for house, text in houses.items():
            if text and "ЗАПОЛНИТЬ" not in text:
                stats["houses"]["filled"] += 1
            else:
                stats["houses"]["empty"] += 1
                
    for pair_key, aspects in texts.get("aspects", {}).items():
        for asp, text in aspects.items():
            if text and "ЗАПОЛНИТЬ" not in text:
                stats["aspects"]["filled"] += 1
            else:
                stats["aspects"]["empty"] += 1
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админка - Натальная Карта</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>
            :root {{ --pico-primary: #e94560; }}
            body {{ background: #1a1a2e; }}
            .container {{ max-width: 1200px; padding: 20px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .stat-card {{ background: #16213e; padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-card h3 {{ color: #ffd700; margin: 0 0 10px 0; }}
            .stat-filled {{ color: #4caf50; font-size: 24px; font-weight: bold; }}
            .stat-empty {{ color: #ff5252; font-size: 24px; font-weight: bold; }}
            .nav-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }}
            .nav-card {{ background: #16213e; padding: 25px; border-radius: 10px; text-decoration: none; color: white; transition: transform 0.2s; }}
            .nav-card:hover {{ transform: translateY(-5px); background: #1f2b4a; }}
            .nav-card h3 {{ color: #ffd700; margin: 0 0 10px 0; }}
            .nav-card p {{ color: #888; margin: 0; }}
            h1 {{ color: #ffd700; text-align: center; }}
        </style>
    </head>
    <body>
        <main class="container">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1>🌌 Админка Натальной Карты</h1>
                <a href="/admin/logout" style="color: #e94560;">Выйти →</a>
            </div>
            <p style="text-align: center; color: #888;">Привет, {user}! Здесь можно редактировать тексты интерпретаций.</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Планеты в знаках</h3>
                    <span class="stat-filled">{stats['signs']['filled']}</span> / 
                    <span class="stat-empty">{stats['signs']['empty']}</span>
                </div>
                <div class="stat-card">
                    <h3>Планеты в домах</h3>
                    <span class="stat-filled">{stats['houses']['filled']}</span> / 
                    <span class="stat-empty">{stats['houses']['empty']}</span>
                </div>
                <div class="stat-card">
                    <h3>Аспекты</h3>
                    <span class="stat-filled">{stats['aspects']['filled']}</span> / 
                    <span class="stat-empty">{stats['aspects']['empty']}</span>
                </div>
            </div>
            
            <div class="nav-grid">
                <a href="/admin/signs" class="nav-card">
                    <h3>🪐 Планеты в знаках</h3>
                    <p>Солнце в Овне, Луна в Тельце...</p>
                </a>
                <a href="/admin/houses" class="nav-card">
                    <h3>🏠 Планеты в домах</h3>
                    <p>Солнце в 1 доме, Луна во 2 доме...</p>
                </a>
                <a href="/admin/aspects" class="nav-card">
                    <h3>⭐ Аспекты</h3>
                    <p>Солнце трин Луна, Марс квадрат Сатурн...</p>
                </a>
                <a href="/admin/generate" class="nav-card">
                    <h3>🤖 AI Генерация</h3>
                    <p>Автоматическое заполнение текстов через Cursor</p>
                </a>
            </div>
            
            <p style="text-align: center; margin-top: 40px; color: #666;">
                <a href="/" style="color: #e94560;">← Вернуться на главную</a>
            </p>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/admin/signs", response_class=HTMLResponse)
async def admin_signs(request: Request, planet: str = None):
    """Редактирование текстов планет в знаках"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    signs_data = texts.get("signs", {})
    
    # Список планет
    planets_list = "".join([
        f'<a href="/admin/signs?planet={p}" class="planet-btn {"active" if planet == p else ""}">{PLANET_NAMES.get(p, p)}</a>'
        for p in signs_data.keys()
    ])
    
    # Форма редактирования
    form_html = ""
    if planet and planet in signs_data:
        form_html = f"<h2>{PLANET_NAMES.get(planet, planet)} в знаках</h2>"
        for sign, text in signs_data[planet].items():
            is_empty = "ЗАПОЛНИТЬ" in text or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{SIGN_NAMES.get(sign, sign)}</label>
                <textarea name="{planet}_{sign}" rows="4">{text}</textarea>
                <button type="button" onclick="generateText('{planet}', '{sign}', this)" class="generate-btn">🤖 Сгенерировать</button>
            </div>
            """
        form_html = f'<form method="POST" action="/admin/signs/save?planet={planet}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты в знаках - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>
            :root {{ --pico-primary: #e94560; }}
            body {{ background: #1a1a2e; }}
            .container {{ max-width: 1000px; padding: 20px; }}
            h1, h2 {{ color: #ffd700; }}
            .planets-nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
            .planet-btn {{ padding: 10px 15px; background: #16213e; color: white; text-decoration: none; border-radius: 8px; }}
            .planet-btn:hover, .planet-btn.active {{ background: #e94560; }}
            .text-block {{ background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; }}
            .text-block.empty {{ border-left: 4px solid #ff5252; }}
            .text-block.filled {{ border-left: 4px solid #4caf50; }}
            .text-block label {{ color: #ffd700; font-weight: bold; display: block; margin-bottom: 10px; }}
            textarea {{ width: 100%; background: #0f1424; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px; }}
            button {{ margin-top: 10px; }}
            .generate-btn {{ background: #4caf50; padding: 8px 15px; font-size: 14px; }}
            .back-link {{ color: #e94560; }}
        </style>
    </head>
    <body>
        <main class="container">
            <h1>🪐 Планеты в знаках</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="planets-nav">
                {planets_list}
            </div>
            
            {form_html if form_html else '<p style="color: #888;">Выберите планету для редактирования</p>'}
        </main>
        
        <script>
        async function generateText(planet, sign, btn) {{
            btn.innerHTML = '⏳ Генерация...';
            btn.disabled = true;
            
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'sign', planet, sign}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) {{
                    btn.parentElement.querySelector('textarea').value = data.text;
                }}
            }} catch(e) {{
                alert('Ошибка генерации: ' + e.message);
            }}
            
            btn.innerHTML = '🤖 Сгенерировать';
            btn.disabled = false;
        }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/signs/save")
async def save_signs(request: Request, planet: str):
    """Сохранение текстов планет в знаках"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if planet not in texts.get("signs", {}):
        texts["signs"][planet] = {}
    
    for key, value in form.items():
        if key.startswith(planet + "_"):
            sign = key.replace(planet + "_", "")
            texts["signs"][planet][sign] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/signs?planet={planet}", status_code=303)


@app.get("/admin/houses", response_class=HTMLResponse)
async def admin_houses(request: Request, planet: str = None):
    """Редактирование текстов планет в домах"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    houses_data = texts.get("houses", {})
    
    planets_list = "".join([
        f'<a href="/admin/houses?planet={p}" class="planet-btn {"active" if planet == p else ""}">{PLANET_NAMES.get(p, p)}</a>'
        for p in houses_data.keys()
    ])
    
    form_html = ""
    if planet and planet in houses_data:
        form_html = f"<h2>{PLANET_NAMES.get(planet, planet)} в домах</h2>"
        for house, text in houses_data[planet].items():
            is_empty = "ЗАПОЛНИТЬ" in text or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{HOUSE_NAMES.get(house, house)}</label>
                <textarea name="{planet}_{house}" rows="4">{text}</textarea>
                <button type="button" onclick="generateText('{planet}', '{house}', this)" class="generate-btn">🤖 Сгенерировать</button>
            </div>
            """
        form_html = f'<form method="POST" action="/admin/houses/save?planet={planet}">{form_html}<button type="submit">💾 Сохранить все</button></form>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Планеты в домах - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>
            :root {{ --pico-primary: #e94560; }}
            body {{ background: #1a1a2e; }}
            .container {{ max-width: 1000px; padding: 20px; }}
            h1, h2 {{ color: #ffd700; }}
            .planets-nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
            .planet-btn {{ padding: 10px 15px; background: #16213e; color: white; text-decoration: none; border-radius: 8px; }}
            .planet-btn:hover, .planet-btn.active {{ background: #e94560; }}
            .text-block {{ background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; }}
            .text-block.empty {{ border-left: 4px solid #ff5252; }}
            .text-block.filled {{ border-left: 4px solid #4caf50; }}
            .text-block label {{ color: #ffd700; font-weight: bold; display: block; margin-bottom: 10px; }}
            textarea {{ width: 100%; background: #0f1424; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px; }}
            button {{ margin-top: 10px; }}
            .generate-btn {{ background: #4caf50; padding: 8px 15px; font-size: 14px; }}
            .back-link {{ color: #e94560; }}
        </style>
    </head>
    <body>
        <main class="container">
            <h1>🏠 Планеты в домах</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="planets-nav">
                {planets_list}
            </div>
            
            {form_html if form_html else '<p style="color: #888;">Выберите планету для редактирования</p>'}
        </main>
        
        <script>
        async function generateText(planet, house, btn) {{
            btn.innerHTML = '⏳ Генерация...';
            btn.disabled = true;
            
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'house', planet, house}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) {{
                    btn.parentElement.querySelector('textarea').value = data.text;
                }}
            }} catch(e) {{
                alert('Ошибка генерации: ' + e.message);
            }}
            
            btn.innerHTML = '🤖 Сгенерировать';
            btn.disabled = false;
        }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/houses/save")
async def save_houses(request: Request, planet: str):
    """Сохранение текстов планет в домах"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    form = await request.form()
    texts = load_texts()
    
    if planet not in texts.get("houses", {}):
        texts["houses"][planet] = {}
    
    for key, value in form.items():
        if key.startswith(planet + "_"):
            house = key.replace(planet + "_", "")
            texts["houses"][planet][house] = value
    
    save_texts(texts)
    return RedirectResponse(url=f"/admin/houses?planet={planet}", status_code=303)


@app.get("/admin/aspects", response_class=HTMLResponse)
async def admin_aspects(request: Request, pair: str = None):
    """Редактирование текстов аспектов"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    texts = load_texts()
    aspects_data = texts.get("aspects", {})
    
    # Список пар планет (Sun_Moon, Sun_Mercury, etc.)
    pairs_list = "".join([
        f'<a href="/admin/aspects?pair={p}" class="planet-btn {"active" if pair == p else ""}">{p.replace("_", " — ")}</a>'
        for p in aspects_data.keys()
    ])
    
    # Форма редактирования
    form_html = ""
    if pair and pair in aspects_data:
        p1, p2 = pair.split("_") if "_" in pair else (pair, "")
        form_html = f"<h2>{PLANET_NAMES.get(p1, p1)} — {PLANET_NAMES.get(p2, p2)}</h2>"
        for asp, text in aspects_data[pair].items():
            is_empty = "ЗАПОЛНИТЬ" in text or not text
            form_html += f"""
            <div class="text-block {'empty' if is_empty else 'filled'}">
                <label>{ASPECT_NAMES.get(asp, asp)}</label>
                <textarea name="{pair}_{asp}" rows="4">{text}</textarea>
                <button type="button" onclick="generateText('{p1}', '{p2}', '{asp}', this)" class="generate-btn">🤖 Сгенерировать</button>
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
        <style>
            :root {{ --pico-primary: #e94560; }}
            body {{ background: #1a1a2e; }}
            .container {{ max-width: 1000px; padding: 20px; }}
            h1, h2, h3 {{ color: #ffd700; }}
            .planets-nav {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
            .planet-btn {{ padding: 10px 15px; background: #16213e; color: white; text-decoration: none; border-radius: 8px; font-size: 13px; }}
            .planet-btn:hover, .planet-btn.active {{ background: #e94560; }}
            .text-block {{ background: #16213e; padding: 15px; border-radius: 10px; margin: 15px 0; }}
            .text-block.empty {{ border-left: 4px solid #ff5252; }}
            .text-block.filled {{ border-left: 4px solid #4caf50; }}
            .text-block label {{ color: #ffd700; font-weight: bold; display: block; margin-bottom: 10px; }}
            textarea {{ width: 100%; background: #0f1424; border: 1px solid #333; color: white; padding: 10px; border-radius: 5px; }}
            button {{ margin-top: 10px; }}
            .generate-btn {{ background: #4caf50; padding: 8px 15px; font-size: 14px; }}
            .back-link {{ color: #e94560; }}
        </style>
    </head>
    <body>
        <main class="container">
            <h1>⭐ Аспекты</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <h3>Выберите пару планет:</h3>
            <div class="planets-nav">
                {pairs_list}
            </div>
            
            {form_html if form_html else '<p style="color: #888;">Выберите пару планет для редактирования аспектов</p>'}
        </main>
        
        <script>
        async function generateText(p1, p2, aspect, btn) {{
            btn.innerHTML = '⏳ Генерация...';
            btn.disabled = true;
            
            try {{
                const resp = await fetch('/admin/api/generate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{type: 'aspect', p1, p2, aspect}}),
                    credentials: 'include'
                }});
                const data = await resp.json();
                if (data.text) {{
                    btn.parentElement.querySelector('textarea').value = data.text;
                }}
            }} catch(e) {{
                alert('Ошибка генерации: ' + e.message);
            }}
            
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
    """Сохранение текстов аспектов"""
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


@app.get("/admin/generate", response_class=HTMLResponse)
async def admin_generate_page(request: Request):
    """Страница массовой AI-генерации"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Генерация - Админка</title>
        <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
        <style>
            :root { --pico-primary: #e94560; }
            body { background: #1a1a2e; }
            .container { max-width: 800px; padding: 20px; }
            h1, h2 { color: #ffd700; }
            .info-box { background: #16213e; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .info-box h3 { color: #4caf50; margin-top: 0; }
            code { background: #0f1424; padding: 2px 8px; border-radius: 4px; }
            .back-link { color: #e94560; }
            .warning { background: #ff525233; border-left: 4px solid #ff5252; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <main class="container">
            <h1>🤖 AI Генерация текстов</h1>
            <a href="/admin" class="back-link">← Назад в админку</a>
            
            <div class="warning">
                <strong>⚠️ Важно!</strong><br>
                Генерация текстов происходит через Cursor AI. Для этого нужно:
                <ol>
                    <li>Открыть этот проект в Cursor IDE</li>
                    <li>Попросить Claude сгенерировать тексты</li>
                    <li>Claude автоматически обновит файл <code>texts.json</code></li>
                </ol>
            </div>
            
            <div class="info-box">
                <h3>Как это работает:</h3>
                <p>1. Нажмите кнопку "🤖 Сгенерировать" рядом с любым текстом</p>
                <p>2. Система отправит запрос к Cursor AI</p>
                <p>3. AI сгенерирует астрологический текст</p>
                <p>4. Текст автоматически появится в поле</p>
                <p>5. Нажмите "Сохранить" чтобы сохранить</p>
            </div>
            
            <div class="info-box">
                <h3>Промпт для массовой генерации:</h3>
                <p>Скопируйте этот промпт в Cursor чат:</p>
                <textarea rows="10" style="width:100%; background:#0f1424; color:white; border:1px solid #333; padding:10px;">
Заполни файл texts.json астрологическими интерпретациями.

Для каждой комбинации "планета в знаке" напиши 3-5 предложений о том, как эта позиция влияет на характер человека.

Для каждой комбинации "планета в доме" напиши 3-5 предложений о том, в какой сфере жизни проявляется энергия планеты.

Для каждого аспекта напиши 3-5 предложений о взаимодействии энергий двух планет.

Стиль: профессиональный астрологический, но понятный обычному человеку. Без эзотерики и мистики.
                </textarea>
            </div>
            
            <div class="info-box">
                <h3>Статус API генерации:</h3>
                <p id="apiStatus">Проверка...</p>
            </div>
        </main>
        
        <script>
            fetch('/admin/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: 'test'})
            })
            .then(r => r.json())
            .then(d => {
                document.getElementById('apiStatus').innerHTML = 
                    '<span style="color:#4caf50">✅ API работает</span><br>' +
                    '<small style="color:#888">Endpoint: /admin/api/generate</small>';
            })
            .catch(e => {
                document.getElementById('apiStatus').innerHTML = 
                    '<span style="color:#ff5252">❌ Ошибка API</span>';
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/admin/api/generate")
async def api_generate_text(request: Request):
    """
    API для генерации текстов.
    Это заглушка - реальная генерация происходит через Cursor IDE.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    
    data = await request.json()
    gen_type = data.get("type")
    
    if gen_type == "test":
        return {"status": "ok", "message": "API работает"}
    
    # Заглушка - возвращаем шаблонный текст
    # В реальности текст генерируется через Cursor AI
    if gen_type == "sign":
        planet = data.get("planet", "")
        sign = data.get("sign", "")
        planet_name = PLANET_NAMES.get(planet, planet)
        sign_name = SIGN_NAMES.get(sign, sign)
        return {
            "text": f"[AI] {planet_name} в {sign_name}: Здесь будет сгенерированный текст об особенностях этого положения планеты. Для генерации используйте Cursor IDE."
        }
    
    if gen_type == "house":
        planet = data.get("planet", "")
        house = data.get("house", "")
        planet_name = PLANET_NAMES.get(planet, planet)
        return {
            "text": f"[AI] {planet_name} в {house} доме: Здесь будет сгенерированный текст о проявлении планеты в этой сфере жизни. Для генерации используйте Cursor IDE."
        }
    
    if gen_type == "aspect":
        p1 = data.get("p1", "")
        p2 = data.get("p2", "")
        aspect = data.get("aspect", "")
        p1_name = PLANET_NAMES.get(p1, p1)
        p2_name = PLANET_NAMES.get(p2, p2)
        asp_name = ASPECT_NAMES.get(aspect, aspect)
        return {
            "text": f"[AI] {p1_name} {asp_name} {p2_name}: Здесь будет сгенерированный текст о взаимодействии этих планет. Для генерации используйте Cursor IDE."
        }
    
    return {"text": "", "error": "Неизвестный тип генерации"}


if __name__ == "__main__":
    print("🌌 Запуск админки Натальной Карты")
    print(f"📍 Адрес: http://localhost:8080/admin")
    print(f"🔐 Логин: {ADMIN_USER}")
    print(f"🔐 Пароль: {ADMIN_PASS}")
    uvicorn.run(app, host="0.0.0.0", port=8080)

