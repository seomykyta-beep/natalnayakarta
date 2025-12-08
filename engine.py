import json
import os
import math
# Используем Loader для явного указания папки
from skyfield.api import Loader, wgs84, load as api_load 
from skyfield.elementslib import osculating_elements_of
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TEXTS_FILE = os.path.join(BASE_DIR, "texts.json")

# Загрузка текстов интерпретаций
def load_interpretation_texts():
    """Загрузка текстов из texts.json"""
    if os.path.exists(TEXTS_FILE):
        with open(TEXTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"signs": {}, "houses": {}, "aspects": {}}

# Загрузка текстов при старте
TEXTS = load_interpretation_texts()

# Создаем загрузчик, указывая папку проекта как хранилище
load = Loader(BASE_DIR)
EPHEMERIS_FILE = 'de421.bsp' # Skyfield сам найдет его в папке Loader-а

# --- DATA SETUP ---
# Если файла нет, Skyfield его скачает
SKYFIELD_AVAILABLE = False
try:
    planets = load(EPHEMERIS_FILE)
    ts = load.timescale()
    earth = planets['earth']
    moon = planets['moon']
    SKYFIELD_AVAILABLE = True
except Exception as e:
    print(f"Error loading astronomy data: {e}")

ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
ZODIAC_ICONS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
PLANET_NAMES = {
    'sun': 'Солнце', 'moon': 'Луна', 'mercury': 'Меркурий', 'venus': 'Венера',
    'mars': 'Марс', 'jupiter barycenter': 'Юпитер', 'saturn barycenter': 'Сатурн',
    'uranus barycenter': 'Уран', 'neptune barycenter': 'Нептун', 'pluto barycenter': 'Плутон',
    'north_node': 'Сев. Узел', 'south_node': 'Южн. Узел', 'lilith': 'Лилит'
}
PLANET_ICONS = {
    'sun': '☉', 'moon': '☾', 'mercury': '☿', 'venus': '♀', 'mars': '♂',
    'jupiter barycenter': '♃', 'saturn barycenter': '♄',
    'uranus barycenter': '♅', 'neptune barycenter': '♆', 'pluto barycenter': '♇',
    'north_node': '☊', 'south_node': '☋', 'lilith': '⚸'
}

# Дефолтные орбисы (можно переопределить через параметры)
DEFAULT_ORBS = {
    0: 8,    # Соединение
    60: 6,   # Секстиль
    90: 8,   # Квадрат
    120: 8,  # Тригон
    150: 4,  # Квинконс
    180: 8   # Оппозиция
}

ASPECTS = {
    0: {"name": "Соединение", "orb": 8, "type": "Conjunction"},
    60: {"name": "Секстиль", "orb": 6, "type": "Sextile"},
    90: {"name": "Квадрат", "orb": 8, "type": "Square"},
    120: {"name": "Тригон", "orb": 8, "type": "Trine"},
    150: {"name": "Квинконс", "orb": 4, "type": "Quincunx"},
    180: {"name": "Оппозиция", "orb": 8, "type": "Opposition"}
}

# === АФЕТИКА: Таблицы достоинств планет ===
# Обитель, Экзальтация, Изгнание, Падение
DIGNITIES = {
    "Sun": {"domicile": ["Leo"], "exaltation": ["Ari"], "detriment": ["Aqu"], "fall": ["Lib"]},
    "Moon": {"domicile": ["Cnc"], "exaltation": ["Tau"], "detriment": ["Cap"], "fall": ["Sco"]},
    "Mercury": {"domicile": ["Gem", "Vir"], "exaltation": ["Vir"], "detriment": ["Sag", "Pis"], "fall": ["Pis"]},
    "Venus": {"domicile": ["Tau", "Lib"], "exaltation": ["Pis"], "detriment": ["Sco", "Ari"], "fall": ["Vir"]},
    "Mars": {"domicile": ["Ari", "Sco"], "exaltation": ["Cap"], "detriment": ["Lib", "Tau"], "fall": ["Cnc"]},
    "Jupiter": {"domicile": ["Sag", "Pis"], "exaltation": ["Cnc"], "detriment": ["Gem", "Vir"], "fall": ["Cap"]},
    "Saturn": {"domicile": ["Cap", "Aqu"], "exaltation": ["Lib"], "detriment": ["Cnc", "Leo"], "fall": ["Ari"]},
    "Uranus": {"domicile": ["Aqu"], "exaltation": ["Sco"], "detriment": ["Leo"], "fall": ["Tau"]},
    "Neptune": {"domicile": ["Pis"], "exaltation": ["Leo"], "detriment": ["Vir"], "fall": ["Aqu"]},
    "Pluto": {"domicile": ["Sco"], "exaltation": ["Ari"], "detriment": ["Tau"], "fall": ["Lib"]}
}

# Баллы за достоинства
DIGNITY_SCORES = {
    "domicile": 5,      # Обитель
    "exaltation": 4,    # Экзальтация
    "detriment": -5,    # Изгнание
    "fall": -4          # Падение
}

def calculate_dignity(planet_key, sign_key):
    """Рассчитывает достоинство планеты в знаке и возвращает статус и баллы."""
    if planet_key not in DIGNITIES:
        return {"status": "", "score": 0}
    
    dignities = DIGNITIES[planet_key]
    
    if sign_key in dignities.get("domicile", []):
        return {"status": "Обитель", "score": DIGNITY_SCORES["domicile"]}
    if sign_key in dignities.get("exaltation", []):
        return {"status": "Экзальтация", "score": DIGNITY_SCORES["exaltation"]}
    if sign_key in dignities.get("detriment", []):
        return {"status": "Изгнание", "score": DIGNITY_SCORES["detriment"]}
    if sign_key in dignities.get("fall", []):
        return {"status": "Падение", "score": DIGNITY_SCORES["fall"]}
    
    return {"status": "", "score": 0}

def calculate_afetics(planets_data, aspects_list):
    """
    Рассчитывает афетику (силу) каждой планеты.
    Учитывает: достоинства, аспекты, угловые дома.
    """
    scores = {}
    
    for planet in planets_data:
        key = planet.get('key')
        if not key or key in ['ASC', 'MC']:
            continue
            
        score = 0
        
        # 1. Достоинства в знаке
        sign_key = planet.get('sign_key', '')
        dignity = calculate_dignity(key, sign_key)
        score += dignity['score']
        
        # 2. Угловые дома (1, 4, 7, 10) дают +3
        house = planet.get('house')
        if house in [1, 4, 7, 10]:
            score += 3
        # Последующие дома (2, 5, 8, 11) дают +2
        elif house in [2, 5, 8, 11]:
            score += 2
        # Падающие дома (3, 6, 9, 12) дают +1
        elif house in [3, 6, 9, 12]:
            score += 1
        
        # 3. Аспекты
        for aspect in aspects_list:
            if aspect['p1_key'] == key or aspect['p2_key'] == key:
                asp_type = aspect['type']
                if asp_type in ['Trine', 'Sextile']:
                    score += 1
                elif asp_type in ['Square', 'Opposition']:
                    score -= 1
                elif asp_type == 'Conjunction':
                    # Соединение с благодетелями (+) или вредителями (-)
                    other_key = aspect['p2_key'] if aspect['p1_key'] == key else aspect['p1_key']
                    if other_key in ['Jupiter', 'Venus']:
                        score += 2
                    elif other_key in ['Saturn', 'Mars']:
                        score -= 1
        
        scores[key] = {
            'score': score,
            'dignity': dignity['status']
        }
    
    return scores

try:
    with open(TEXTS_FILE, "r", encoding="utf-8") as f: TEXTS = json.load(f)
except: TEXTS = {}

def get_text(category, key1, key2=None, gender="general"):
    """Получение текста с учётом пола (gender: general/male/female)"""
    try:
        if category == "signs":
            data = TEXTS.get('signs', {}).get(key1, {}).get(key2, "")
            if isinstance(data, dict):
                # Новая структура с разделением по полу
                return data.get(gender, data.get('general', ''))
            return data  # Старая структура (просто строка)
        if category == "houses":
            data = TEXTS.get('houses', {}).get(key1, {}).get(str(key2), "")
            if isinstance(data, dict):
                return data.get(gender, data.get('general', ''))
            return data
        if category == "aspects":
            return TEXTS.get('aspects', {}).get(f"{key1}_{key2}", {}).get(key2, "")
    except: return ""
    return ""

def get_interpretation(planet_key, sign, gender="general"):
    """Получение интерпретации планеты в знаке с учётом пола"""
    json_key = planet_key.capitalize()
    if "barycenter" in planet_key: json_key = planet_key.split()[0].capitalize()
    
    data = TEXTS.get('signs', {}).get(json_key, {}).get(sign, "")
    
    if isinstance(data, dict):
        # Новая структура с разделением по полу
        text = data.get(gender, data.get('general', ''))
    else:
        text = data  # Старая структура
    
    if not text: 
        return f"Трактовка для {PLANET_NAMES.get(planet_key, planet_key)} в знаке {sign}."
    return text

def degrees_to_zodiac(lon):
    lon = lon % 360
    index = int(lon / 30)
    degree = lon % 30
    sign_keys = ["Ari", "Tau", "Gem", "Cnc", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
    return ZODIAC_SIGNS[index], round(degree, 2), ZODIAC_ICONS[index], sign_keys[index]

def get_city_info(city_name, lat=None, lon=None):
    tf = TimezoneFinder()
    if lat and lon: return lat, lon, tf.timezone_at(lng=lon, lat=lat)
    try:
        geolocator = Nominatim(user_agent="astro_bot_v4")
        loc = geolocator.geocode(city_name, language='ru')
        if loc: return loc.latitude, loc.longitude, tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
    except: pass
    return None, None, None

def get_house_placement(planet_lon, houses):
    for i in range(12):
        start = houses[i]
        end = houses[(i + 1) % 12]
        if start < end:
            if start <= planet_lon < end:
                return i + 1
        else: # House crosses 0 degrees
            if start <= planet_lon or planet_lon < end:
                return i + 1
    return 1

def calculate_houses(t, lat, lon):
    # Standard Equal Houses from ASC (Fallback)
    gast = t.gast
    lst = (gast + lon / 15.0) % 24
    ramc = math.radians(lst * 15)
    eps = math.radians(23.44)
    lat_rad = math.radians(lat)
    
    # MC
    mc_rad = math.atan2(math.tan(ramc), math.cos(eps))
    mc = math.degrees(mc_rad) % 360
    if mc < 0: mc += 360
    if abs(mc - (lst*15)) > 90: mc = (mc + 180) % 360
    
    # ASC
    asc_rad = math.atan2(math.cos(ramc), -math.sin(ramc) * math.cos(eps) - math.tan(lat_rad) * math.sin(eps))
    asc = math.degrees(asc_rad) % 360
    
    houses = []
    for i in range(12): houses.append((asc + i * 30) % 360)
    return houses

def calculate_placidus_houses(t, lat, lon):
    """
    Calculates Placidus house cusps using iterative algorithm in pure Python.
    Based on standard astrological formulas (M. Munkasey).
    """
    # Convert inputs
    gast = t.gast
    ra_ramc = (gast + lon / 15.0) % 24
    ramc = math.radians(ra_ramc * 15)
    eps = math.radians(23.44) # Obliquity
    lat_rad = math.radians(lat)

    # 1. MC & ASC
    mc_rad = math.atan2(math.tan(ramc), math.cos(eps))
    mc = math.degrees(mc_rad) % 360
    if mc < 0: mc += 360
    # Correct quadrant for MC
    if abs(mc - (ra_ramc * 15)) > 90:
        mc = (mc + 180) % 360
    
    asc_rad = math.atan2(math.cos(ramc), -math.sin(ramc) * math.cos(eps) - math.tan(lat_rad) * math.sin(eps))
    asc = math.degrees(asc_rad) % 360

    # 2. Intermediate Cusps (11, 12, 2, 3) via Iteration
    houses = [0] * 12
    houses[0] = asc
    houses[9] = mc
    houses[6] = (asc + 180) % 360
    houses[3] = (mc + 180) % 360

    def iterate_house(offset_deg, factor):
        # Initial guess: RAMC + offset
        r = ramc + math.radians(offset_deg)
        for _ in range(50): # Max iterations
            try:
                decl = math.atan(math.tan(eps) * math.sin(r))
                ad = math.asin(math.tan(lat_rad) * math.tan(decl))
                new_r = ramc + math.radians(offset_deg) + factor * ad
            except:
                return None
            
            if abs(new_r - r) < 1e-6:
                r = new_r
                break
            r = new_r
            
        # Convert RA back to Longitude (Cusp)
        cusp_rad = math.atan2(math.tan(r), math.cos(eps))
        cusp_deg = math.degrees(cusp_rad) % 360
        return cusp_deg

    h11 = iterate_house(30, 1/3)
    h12 = iterate_house(60, 2/3)
    h2  = iterate_house(120, 2/3) 
    h3  = iterate_house(150, 1/3)

    if lat > 66 or lat < -66 or h11 is None:
        return calculate_houses(t, lat, lon)

    houses[10] = h11
    houses[11] = h12
    houses[1] = h2
    houses[2] = h3
    
    houses[4] = (houses[10] + 180) % 360
    houses[5] = (houses[11] + 180) % 360
    houses[7] = (houses[1] + 180) % 360
    houses[8] = (houses[2] + 180) % 360
    
    return houses

def get_transit_text(transit_planet_key, aspect_type):
    """Получает текст интерпретации транзита из texts.json"""
    key = f"tr_{transit_planet_key}_{aspect_type}"
    return TEXTS.get('transits', {}).get(key, "")

def find_aspects(planets_data, custom_orbs=None):
    """
    Находит аспекты между планетами.
    custom_orbs: dict {angle: orb} для переопределения орбисов
    """
    orbs = DEFAULT_ORBS.copy()
    if custom_orbs:
        orbs.update(custom_orbs)
    
    aspects_list = []
    for i in range(len(planets_data)):
        for j in range(i + 1, len(planets_data)):
            p1 = planets_data[i]
            p2 = planets_data[j]
            diff = abs(p1['abs_pos'] - p2['abs_pos'])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                orb = orbs.get(angle, data['orb'])
                if abs(diff - angle) <= orb:
                    # Получаем текст аспекта из texts.json
                    p1_key = p1.get('key', '')
                    p2_key = p2.get('key', '')
                    aspect_key = f"{p1_key}_{p2_key}"
                    aspect_text = TEXTS.get('aspects', {}).get(aspect_key, {}).get(data['type'], "")
                    if not aspect_text:
                        aspect_text = f"Аспект {data['name']} между {p1['name']} и {p2['name']} ({round(diff,1)}°)"
                    
                    aspects_list.append({
                        "p1": p1['name'],
                        "p2": p2['name'],
                        "p1_key": p1_key,
                        "p2_key": p2_key,
                        "type": data['type'],
                        "name": data['name'],
                        "orb": round(abs(diff - angle), 2),
                        "exact_orb": round(diff, 2),
                        "text": aspect_text
                    })
    return aspects_list


def find_transit_aspects(natal_planets, transit_planets, custom_orbs=None):
    """
    Находит аспекты между натальными и транзитными планетами.
    custom_orbs: dict {angle: orb} для переопределения орбисов
    """
    orbs = DEFAULT_ORBS.copy()
    if custom_orbs:
        orbs.update(custom_orbs)
    
    aspects_list = []
    for p1 in natal_planets:
        for p2 in transit_planets:
            diff = abs(p1['abs_pos'] - p2['abs_pos'])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                orb = orbs.get(angle, data['orb'])
                if abs(diff - angle) <= orb:
                    # Получаем транзитный текст
                    transit_text = get_transit_text(p2.get('key', ''), data['type'])
                    if not transit_text:
                        transit_text = f"Транзит {p2['name']} {data['name']} натальный {p1['name']}"
                    
                    aspects_list.append({
                        "p1": p1['name'],  # Натальная
                        "p2": p2['name'],  # Транзитная
                        "p1_key": p1.get('key'),
                        "p2_key": p2.get('key'),
                        "type": data['type'],
                        "name": data['name'],
                        "orb": round(abs(diff - angle), 2),
                        "exact_orb": round(diff, 2),
                        "text": transit_text,
                        "is_transit": True
                    })
    return aspects_list

def build_chart(local_dt, latitude, longitude, city_label, gender="male"):
    t = ts.from_datetime(local_dt)
    try:
        houses = calculate_placidus_houses(t, latitude, longitude)
    except:
        houses = calculate_houses(t, latitude, longitude)

    asc_sign, asc_deg, _, _ = degrees_to_zodiac(houses[0])
    target_planets = [
        'sun', 'moon', 'mercury', 'venus', 'mars',
        'jupiter barycenter', 'saturn barycenter', 'uranus barycenter',
        'neptune barycenter', 'pluto barycenter'
    ]
    observer = earth + wgs84.latlon(latitude, longitude)

    planets_data = []
    for p_name in target_planets:
        body = planets[p_name]
        astrometric = observer.at(t).observe(body)
        _, lon_val, _ = astrometric.ecliptic_latlon()
        deg = lon_val.degrees % 360

        t_next = ts.from_datetime(local_dt + timedelta(minutes=1))
        lon_next = observer.at(t_next).observe(body).ecliptic_latlon()[1].degrees % 360
        is_retro = abs(deg - lon_next) < 180 and lon_next < deg

        sign_name, sign_deg, _, sign_key = degrees_to_zodiac(deg)
        p_key = p_name.split()[0].capitalize()
        house_num = get_house_placement(deg, houses)
        text_sign = get_interpretation(p_name, sign_key, gender)
        text_house = get_text('houses', p_key, house_num, gender) or f" (Дом {house_num})"

        planets_data.append({
            'name': PLANET_NAMES[p_name],
            'key': p_key,
            'icon': PLANET_ICONS[p_name],
            'sign': sign_name,
            'sign_key': sign_key,
            'pos': round(sign_deg, 2),
            'abs_pos': deg,
            'house': house_num,
            'text': f"{text_sign}\\n{text_house}",
            'is_retro': bool(is_retro)
        })

    try:
        moon_pos = earth.at(t).observe(moon)
        elements = osculating_elements_of(moon_pos)
        node_deg = elements.longitude_of_ascending_node.degrees % 360
        sign_name, sign_deg, _, sign_key = degrees_to_zodiac(node_deg)
        house_num = get_house_placement(node_deg, houses)
        dt_past = ts.from_datetime(local_dt - timedelta(minutes=1))
        node_past = osculating_elements_of(earth.at(dt_past).observe(moon)).longitude_of_ascending_node.degrees % 360
        is_retro = (node_deg < node_past) if abs(node_deg - node_past) < 180 else (node_deg > node_past)

        planets_data.append({
            'name': PLANET_NAMES['north_node'],
            'key': 'North_node',
            'icon': PLANET_ICONS['north_node'],
            'sign': sign_name,
            'sign_key': sign_key,
            'pos': round(sign_deg, 2),
            'abs_pos': node_deg,
            'house': house_num,
            'text': 'Кармическая задача',
            'is_retro': bool(is_retro)
        })

        s_node_deg = (node_deg + 180) % 360
        sign_name, sign_deg, _, sign_key = degrees_to_zodiac(s_node_deg)
        house_num = get_house_placement(s_node_deg, houses)
        planets_data.append({
            'name': PLANET_NAMES['south_node'],
            'key': 'South_node',
            'icon': PLANET_ICONS['south_node'],
            'sign': sign_name,
            'sign_key': sign_key,
            'pos': round(sign_deg, 2),
            'abs_pos': s_node_deg,
            'house': house_num,
            'text': 'Прошлый опыт',
            'is_retro': bool(is_retro)
        })

        w = elements.argument_of_periapsis.degrees
        lilith_deg = (node_deg + w + 180) % 360
        sign_name, sign_deg, _, sign_key = degrees_to_zodiac(lilith_deg)
        house_num = get_house_placement(lilith_deg, houses)
        planets_data.append({
            'name': PLANET_NAMES['lilith'],
            'key': 'Lilith',
            'icon': PLANET_ICONS['lilith'],
            'sign': sign_name,
            'sign_key': sign_key,
            'pos': round(sign_deg, 2),
            'abs_pos': lilith_deg,
            'house': house_num,
            'text': 'Теневая сторона',
            'is_retro': False
        })
    except Exception as e:
        print(f"Error calculating Nodes/Lilith: {e}")

    planets_data.insert(0, {
        'name': 'Асцендент',
        'key': 'ASC',
        'icon': '⬆️',
        'sign': asc_sign,
        'pos': asc_deg,
        'abs_pos': houses[0],
        'house': 'ASC',
        'text': 'Ваше внешнее Я',
        'is_retro': False
    })

    mc_sign, mc_deg, _, _ = degrees_to_zodiac(houses[9])
    planets_data.insert(1, {
        'name': 'Сер. Неба',
        'key': 'MC',
        'icon': 'M',
        'sign': mc_sign,
        'pos': mc_deg,
        'abs_pos': houses[9],
        'house': 'MC',
        'text': 'Цель жизни',
        'is_retro': False
    })

    aspects = find_aspects(planets_data)
    
    # Рассчитываем афетику (силу планет)
    afetics = calculate_afetics(planets_data, aspects)
    
    # Добавляем данные афетики к каждой планете
    for planet in planets_data:
        key = planet.get('key')
        if key and key in afetics:
            planet['afetic_score'] = afetics[key]['score']
            planet['dignity'] = afetics[key]['dignity']
        else:
            planet['afetic_score'] = 0
            planet['dignity'] = ''
    
    meta = {
        'city': city_label,
        'coords': f"{latitude:.2f}, {longitude:.2f}",
        'dt': local_dt.strftime('%d.%m.%Y %H:%M')
    }
    return {'planets': planets_data, 'houses': houses, 'aspects': aspects, 'meta': meta, 'afetics': afetics}


def calculate_real_chart(name, year, month, day, hour, minute, city,
                         lat=None, lon=None,
                         transit_year=None, transit_month=None, transit_day=None,
                         transit_hour=None, transit_minute=None,
                         custom_orbs=None, gender="male"):
    if not SKYFIELD_AVAILABLE:
        return {
            'name': name,
            'gender': gender,
            'planets': [],
            'aspects': [],
            'houses': [0]*12,
            'meta': {'city': 'Error', 'coords': '0,0', 'dt': 'System Unavailable'},
            'error': 'Skyfield data not loaded'
        }

    r_lat, r_lon, tz_str = get_city_info(city, lat, lon)
    if not r_lat:
        r_lat, r_lon, tz_str = 55.75, 37.61, 'Europe/Moscow'

    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    natal_dt = tz.localize(datetime(year, month, day, hour, minute))
    natal_chart = build_chart(natal_dt, r_lat, r_lon, city, gender=gender)

    # Пересчитываем аспекты с учетом пользовательских орбисов
    if custom_orbs:
        natal_chart['aspects'] = find_aspects(natal_chart['planets'], custom_orbs)
    
    result = {
        'name': name,
        'gender': gender,
        'planets': natal_chart['planets'],
        'aspects': natal_chart['aspects'],
        'houses': natal_chart['houses'],
        'meta': natal_chart['meta'],
        'afetics': natal_chart.get('afetics', {}),
        'orbs_used': custom_orbs or DEFAULT_ORBS
    }

    transit_fields = [transit_year, transit_month, transit_day, transit_hour, transit_minute]
    if all(v is not None for v in transit_fields):
        transit_dt = tz.localize(datetime(transit_year, transit_month, transit_day, transit_hour, transit_minute))
        transit_chart = build_chart(transit_dt, r_lat, r_lon, city, gender=gender)
        result['transits'] = transit_chart['planets']
        result['transit_meta'] = transit_chart['meta']
        result['transit_aspects'] = find_transit_aspects(natal_chart['planets'], transit_chart['planets'], custom_orbs)
    else:
        result['transits'] = []
        result['transit_meta'] = None
        result['transit_aspects'] = []

    return result

def generate_pdf(user_data):
    """Генерация PDF отчёта с помощью reportlab"""
    if not os.path.exists(REPORTS_DIR): 
        os.makedirs(REPORTS_DIR)
    
    # Словарь перевода аспектов
    ASPECT_RU = {
        'Conjunction': 'Соединение',
        'Sextile': 'Секстиль',
        'Square': 'Квадрат',
        'Trine': 'Тригон',
        'Quincunx': 'Квинконс',
        'Opposition': 'Оппозиция'
    }
    
    # Безопасное имя файла (только латиница и цифры)
    safe_name = "".join(c for c in user_data.get('name', 'report') if c.isalnum() or c in ' _-').strip()
    if not safe_name:
        safe_name = 'report'
    pdf_path = os.path.join(REPORTS_DIR, f"report_{safe_name}.pdf")
    
    # Регистрация шрифта с поддержкой кириллицы
    FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
    font_name = 'Helvetica'  # По умолчанию
    
    if os.path.exists(FONT_PATH):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
            font_name = 'DejaVu'
        except Exception as e:
            print(f"Font registration error: {e}")
    
    try:
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 40*mm
        
        # Заголовок
        c.setFont(font_name, 18)
        name = user_data.get('name', 'Без имени')
        c.drawString(20*mm, y, f"Натальная карта: {name}")
        y -= 10*mm
        
        # Мета-информация
        c.setFont(font_name, 11)
        meta = user_data.get('meta', {})
        city = meta.get('city', '-')
        dt = meta.get('dt', '-')
        c.drawString(20*mm, y, f"Город: {city} | Дата: {dt}")
        y -= 8*mm
        
        gender = user_data.get('gender', 'general')
        gender_text = {'male': 'Мужчина', 'female': 'Женщина'}.get(gender, 'Не указан')
        c.drawString(20*mm, y, f"Пол: {gender_text}")
        y -= 12*mm
        
        # Планеты
        c.setFont(font_name, 14)
        c.drawString(20*mm, y, "Планеты в знаках:")
        y -= 8*mm
        
        c.setFont(font_name, 10)
        for p in user_data.get('planets', []):
            if y < 30*mm:
                c.showPage()
                c.setFont(font_name, 10)
                y = height - 30*mm
            
            # Планета и позиция (без иконок-эмодзи, они могут не отображаться)
            p_name = p.get('name', '')
            p_sign = p.get('sign', '')
            p_pos = p.get('pos', '')
            line = f"{p_name}: {p_sign} {p_pos}"
            c.drawString(20*mm, y, line)
            y -= 5*mm
            
            # Интерпретация (если есть)
            text = p.get('text', '')
            if text and len(text) > 5:
                # Убираем переносы строк и лишние пробелы
                text = ' '.join(text.replace('\\n', ' ').split())
                # Разбиваем длинный текст на строки
                words = text.split()
                current_line = ""
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if len(test_line) < 85:
                        current_line = test_line
                    else:
                        if y < 30*mm:
                            c.showPage()
                            c.setFont(font_name, 10)
                            y = height - 30*mm
                        c.setFillColorRGB(0.4, 0.4, 0.4)
                        c.drawString(25*mm, y, current_line)
                        y -= 4*mm
                        current_line = word
                if current_line:
                    if y < 30*mm:
                        c.showPage()
                        c.setFont(font_name, 10)
                        y = height - 30*mm
                    c.setFillColorRGB(0.4, 0.4, 0.4)
                    c.drawString(25*mm, y, current_line)
                    y -= 4*mm
                c.setFillColorRGB(0, 0, 0)
            y -= 3*mm
        
        # Аспекты
        y -= 5*mm
        if y < 50*mm:
            c.showPage()
            y = height - 30*mm
        
        c.setFont(font_name, 14)
        c.drawString(20*mm, y, "Аспекты:")
        y -= 8*mm
        
        c.setFont(font_name, 10)
        for a in user_data.get('aspects', []):
            if y < 20*mm:
                c.showPage()
                c.setFont(font_name, 10)
                y = height - 30*mm
            
            # Переводим тип аспекта на русский
            asp_type = a.get('type', '')
            asp_type_ru = ASPECT_RU.get(asp_type, asp_type)
            
            p1 = a.get('p1', '')
            p2 = a.get('p2', '')
            orb = a.get('orb', '')
            
            line = f"- {p1} {asp_type_ru} {p2} ({orb})"
            c.drawString(20*mm, y, line)
            y -= 5*mm
        
        c.save()
        return pdf_path
    except Exception as e:
        print(f"PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


# === SOLAR RETURN (СОЛЯР) ===
def find_solar_return(natal_sun_pos, target_year, latitude, longitude, tz_str, natal_month, natal_day):
    """
    Находит момент соляра - когда Солнце возвращается в натальную позицию.
    natal_sun_pos: абсолютная позиция Солнца в натале (0-360)
    target_year: год для соляра
    """
    if not SKYFIELD_AVAILABLE:
        return None
    
    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    
    # Начинаем поиск за день до дня рождения
    search_start = tz.localize(datetime(target_year, natal_month, natal_day, 0, 0)) - timedelta(days=1)
    
    # Бинарный поиск момента возвращения
    t_start = ts.from_datetime(search_start.astimezone(pytz.UTC))
    
    best_time = None
    best_diff = 360
    
    # Грубый поиск (по часам)
    for hours in range(72):  # 3 дня
        current_dt = search_start + timedelta(hours=hours)
        t = ts.from_datetime(current_dt.astimezone(pytz.UTC))
        astrometric = earth.at(t).observe(planets['sun'])
        apparent = astrometric.apparent()
        lat_ecl, lon_ecl, _ = apparent.ecliptic_latlon()
        sun_pos = lon_ecl.degrees % 360
        
        diff = abs(sun_pos - natal_sun_pos)
        if diff > 180:
            diff = 360 - diff
        
        if diff < best_diff:
            best_diff = diff
            best_time = current_dt
    
    # Точный поиск (по минутам) вокруг лучшего времени
    if best_time:
        for minutes in range(-60, 61):
            current_dt = best_time + timedelta(minutes=minutes)
            t = ts.from_datetime(current_dt.astimezone(pytz.UTC))
            astrometric = earth.at(t).observe(planets['sun'])
            apparent = astrometric.apparent()
            lat_ecl, lon_ecl, _ = apparent.ecliptic_latlon()
            sun_pos = lon_ecl.degrees % 360
            
            diff = abs(sun_pos - natal_sun_pos)
            if diff > 180:
                diff = 360 - diff
            
            if diff < best_diff:
                best_diff = diff
                best_time = current_dt
    
    return best_time


# === LUNAR RETURN (ЛУНАР) ===
def find_lunar_return(natal_moon_pos, target_year, target_month, latitude, longitude, tz_str):
    """
    Находит момент лунара - когда Луна возвращается в натальную позицию.
    natal_moon_pos: абсолютная позиция Луны в натале (0-360)
    target_year, target_month: месяц для лунара
    """
    if not SKYFIELD_AVAILABLE:
        return None
    
    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    
    # Начинаем с 1-го числа месяца
    search_start = tz.localize(datetime(target_year, target_month, 1, 0, 0))
    
    best_time = None
    best_diff = 360
    
    # Грубый поиск (по часам) - лунный месяц ~27.3 дня
    for hours in range(31 * 24):  # весь месяц
        current_dt = search_start + timedelta(hours=hours)
        t = ts.from_datetime(current_dt.astimezone(pytz.UTC))
        astrometric = earth.at(t).observe(moon)
        apparent = astrometric.apparent()
        lat_ecl, lon_ecl, _ = apparent.ecliptic_latlon()
        moon_pos = lon_ecl.degrees % 360
        
        diff = abs(moon_pos - natal_moon_pos)
        if diff > 180:
            diff = 360 - diff
        
        if diff < best_diff:
            best_diff = diff
            best_time = current_dt
    
    # Точный поиск (по минутам)
    if best_time:
        for minutes in range(-60, 61):
            current_dt = best_time + timedelta(minutes=minutes)
            t = ts.from_datetime(current_dt.astimezone(pytz.UTC))
            astrometric = earth.at(t).observe(moon)
            apparent = astrometric.apparent()
            lat_ecl, lon_ecl, _ = apparent.ecliptic_latlon()
            moon_pos = lon_ecl.degrees % 360
            
            diff = abs(moon_pos - natal_moon_pos)
            if diff > 180:
                diff = 360 - diff
            
            if diff < best_diff:
                best_diff = diff
                best_time = current_dt
    
    return best_time


# === UNIFIED CHART CALCULATION (для всех режимов) ===
def calculate_chart_with_mode(name, year, month, day, hour, minute, city,
                              lat=None, lon=None, gender="male", mode="natal",
                              # Transit params
                              transit_year=None, transit_month=None, transit_day=None,
                              transit_hour=None, transit_minute=None,
                              # Solar params
                              solar_year=None, solar_city=None, solar_lat=None, solar_lon=None,
                              # Lunar params
                              lunar_year=None, lunar_month=None, lunar_city=None, lunar_lat=None, lunar_lon=None,
                              custom_orbs=None):
    """
    Универсальный расчёт карты с поддержкой режимов:
    - natal: натальная карта + транзиты
    - solar: натальная карта + соляр
    - lunar: натальная карта + лунар
    """
    if not SKYFIELD_AVAILABLE:
        return {
            'name': name,
            'gender': gender,
            'planets': [],
            'aspects': [],
            'houses': [0]*12,
            'meta': {'city': 'Error', 'coords': '0,0', 'dt': 'System Unavailable'},
            'error': 'Skyfield data not loaded'
        }

    # Получаем координаты для натала
    r_lat, r_lon, tz_str = get_city_info(city, lat, lon)
    if not r_lat:
        r_lat, r_lon, tz_str = 55.75, 37.61, 'Europe/Moscow'

    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    natal_dt = tz.localize(datetime(year, month, day, hour, minute))
    natal_chart = build_chart(natal_dt, r_lat, r_lon, city, gender=gender)

    if custom_orbs:
        natal_chart['aspects'] = find_aspects(natal_chart['planets'], custom_orbs)
    
    result = {
        'name': name,
        'gender': gender,
        'mode': mode,
        'planets': natal_chart['planets'],
        'aspects': natal_chart['aspects'],
        'houses': natal_chart['houses'],
        'meta': natal_chart['meta'],
        'afetics': natal_chart.get('afetics', {}),
        'orbs_used': custom_orbs or DEFAULT_ORBS
    }

    # === РЕЖИМ НАТАЛ + ТРАНЗИТЫ ===
    if mode == 'natal':
        transit_fields = [transit_year, transit_month, transit_day, transit_hour, transit_minute]
        if all(v is not None for v in transit_fields):
            transit_dt = tz.localize(datetime(transit_year, transit_month, transit_day, transit_hour, transit_minute))
            transit_chart = build_chart(transit_dt, r_lat, r_lon, city, gender=gender)
            result['transits'] = transit_chart['planets']
            result['transit_meta'] = transit_chart['meta']
            result['transit_aspects'] = find_transit_aspects(natal_chart['planets'], transit_chart['planets'], custom_orbs)
        else:
            result['transits'] = []
            result['transit_meta'] = None
            result['transit_aspects'] = []
    
    # === РЕЖИМ СОЛЯР ===
    elif mode == 'solar' and solar_year:
        # Находим натальную позицию Солнца
        natal_sun = next((p for p in natal_chart['planets'] if p['key'] == 'Sun'), None)
        if natal_sun:
            natal_sun_pos = natal_sun['abs_pos']
            
            # Координаты для соляра
            s_lat = solar_lat or r_lat
            s_lon = solar_lon or r_lon
            s_city = solar_city or city
            
            # Получаем timezone для места соляра
            _, _, s_tz_str = get_city_info(s_city, s_lat, s_lon)
            if not s_tz_str:
                s_tz_str = tz_str
            
            # Находим момент соляра
            solar_dt = find_solar_return(natal_sun_pos, solar_year, s_lat, s_lon, s_tz_str, month, day)
            
            if solar_dt:
                solar_chart = build_chart(solar_dt, s_lat, s_lon, s_city, gender=gender)
                result['outer_planets'] = solar_chart['planets']
                result['outer_meta'] = solar_chart['meta']
                result['outer_houses'] = solar_chart['houses']
                result['transit_aspects'] = find_transit_aspects(natal_chart['planets'], solar_chart['planets'], custom_orbs)
            else:
                result['outer_planets'] = []
                result['outer_meta'] = None
                result['transit_aspects'] = []
    
    # === РЕЖИМ ЛУНАР ===
    elif mode == 'lunar' and lunar_year and lunar_month:
        # Находим натальную позицию Луны
        natal_moon = next((p for p in natal_chart['planets'] if p['key'] == 'Moon'), None)
        if natal_moon:
            natal_moon_pos = natal_moon['abs_pos']
            
            # Координаты для лунара
            l_lat = lunar_lat or r_lat
            l_lon = lunar_lon or r_lon
            l_city = lunar_city or city
            
            # Получаем timezone для места лунара
            _, _, l_tz_str = get_city_info(l_city, l_lat, l_lon)
            if not l_tz_str:
                l_tz_str = tz_str
            
            # Находим момент лунара
            lunar_dt = find_lunar_return(natal_moon_pos, lunar_year, lunar_month, l_lat, l_lon, l_tz_str)
            
            if lunar_dt:
                lunar_chart = build_chart(lunar_dt, l_lat, l_lon, l_city, gender=gender)
                result['outer_planets'] = lunar_chart['planets']
                result['outer_meta'] = lunar_chart['meta']
                result['outer_houses'] = lunar_chart['houses']
                result['transit_aspects'] = find_transit_aspects(natal_chart['planets'], lunar_chart['planets'], custom_orbs)
            else:
                result['outer_planets'] = []
                result['outer_meta'] = None
                result['transit_aspects'] = []

    return result
