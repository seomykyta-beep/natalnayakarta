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
from xhtml2pdf import pisa

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

ASPECTS = {
    0: {"name": "Соединение", "orb": 8, "type": "Conjunction"},
    60: {"name": "Секстиль", "orb": 6, "type": "Sextile"},
    90: {"name": "Квадрат", "orb": 8, "type": "Square"},
    120: {"name": "Тригон", "orb": 8, "type": "Trine"},
    150: {"name": "Квинконс", "orb": 4, "type": "Quincunx"},
    180: {"name": "Оппозиция", "orb": 8, "type": "Opposition"}
}

try:
    with open(TEXTS_FILE, "r", encoding="utf-8") as f: TEXTS = json.load(f)
except: TEXTS = {}

def get_text(category, key1, key2=None):
    try:
        if category == "signs": return TEXTS.get('signs', {}).get(key1, {}).get(key2, "")
        if category == "houses": return TEXTS.get('houses', {}).get(key1, {}).get(str(key2), "")
        if category == "aspects": return TEXTS.get('aspects', {}).get(f"{key1}_{key2}", {}).get(key2, "")
    except: return ""
    return ""

def get_interpretation(planet_key, sign):
    json_key = planet_key.capitalize()
    if "barycenter" in planet_key: json_key = planet_key.split()[0].capitalize()
    text = TEXTS['signs'].get(json_key, {}).get(sign, "")
    if not text: return f"Трактовка для {PLANET_NAMES.get(planet_key, planet_key)} в знаке {sign}."
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

def find_aspects(planets_data):
    aspects_list = []
    for i in range(len(planets_data)):
        for j in range(i + 1, len(planets_data)):
            p1 = planets_data[i]
            p2 = planets_data[j]
            diff = abs(p1['abs_pos'] - p2['abs_pos'])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                if abs(diff - angle) <= data['orb']:
                    aspects_list.append({
                        "p1": p1['name'],
                        "p2": p2['name'],
                        "p1_key": p1.get('key'),
                        "p2_key": p2.get('key'),
                        "type": data['type'],
                        "name": data['name'],
                        "orb": round(abs(diff - angle), 2),
                        "text": f"Аспект {data['name']} ({round(diff,1)}°)"
                    })
    return aspects_list


def find_transit_aspects(natal_planets, transit_planets):
    aspects_list = []
    for p1 in natal_planets:
        for p2 in transit_planets:
            diff = abs(p1['abs_pos'] - p2['abs_pos'])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                if abs(diff - angle) <= data['orb']:
                    aspects_list.append({
                        "p1": p1['name'],
                        "p2": p2['name'],
                        "p1_key": p1.get('key'),
                        "p2_key": p2.get('key'),
                        "type": data['type'],
                        "name": data['name'],
                        "orb": round(abs(diff - angle), 2),
                        "text": f"Аспект {data['name']} ({round(diff,1)}°)"
                    })
    return aspects_list

def build_chart(local_dt, latitude, longitude, city_label):
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
        text_sign = get_interpretation(p_name, sign_key)
        text_house = get_text('houses', p_key, house_num) or f" (Дом {house_num})"

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
    meta = {
        'city': city_label,
        'coords': f"{latitude:.2f}, {longitude:.2f}",
        'dt': local_dt.strftime('%d.%m.%Y %H:%M')
    }
    return {'planets': planets_data, 'houses': houses, 'aspects': aspects, 'meta': meta}


def calculate_real_chart(name, year, month, day, hour, minute, city,
                         lat=None, lon=None,
                         transit_year=None, transit_month=None, transit_day=None,
                         transit_hour=None, transit_minute=None):
    if not SKYFIELD_AVAILABLE:
        return {
            'name': name,
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
    natal_chart = build_chart(natal_dt, r_lat, r_lon, city)

    result = {
        'name': name,
        'planets': natal_chart['planets'],
        'aspects': natal_chart['aspects'],
        'houses': natal_chart['houses'],
        'meta': natal_chart['meta']
    }

    transit_fields = [transit_year, transit_month, transit_day, transit_hour, transit_minute]
    if all(v is not None for v in transit_fields):
        transit_dt = tz.localize(datetime(transit_year, transit_month, transit_day, transit_hour, transit_minute))
        transit_chart = build_chart(transit_dt, r_lat, r_lon, city)
        result['transits'] = transit_chart['planets']
        result['transit_meta'] = transit_chart['meta']
        result['transit_aspects'] = find_transit_aspects(natal_chart['planets'], transit_chart['planets'])
    else:
        result['transits'] = []
        result['transit_meta'] = None
        result['transit_aspects'] = []

    return result

def generate_pdf(user_data):
    if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
    pdf_path = os.path.join(REPORTS_DIR, f"report_{user_data['name']}.pdf")
    
    FONT_REGULAR = os.path.join(BASE_DIR, "DejaVuSans.ttf")

    rows = ""
    for p in user_data['planets']:
        rows += f"""<div class="planet"><b>{p['icon']} {p['name']}</b>: {p['sign']} {p['pos']}°<br><small>{p['text']}</small></div>"""
    
    aspects_html = ""
    for a in user_data['aspects']:
        aspects_html += f"<div>• {a['p1']} {a['type']} {a['p2']}</div>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{ font-family: 'DejaVu'; src: url('{FONT_REGULAR}'); }}
            body {{ font-family: 'DejaVu', sans-serif; }}
            .planet {{ margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        <h1>Карта: {user_data['name']}</h1>
        <p>{user_data['meta']['city']} / {user_data['meta']['dt']}</p>
        {rows}
        <h3>Аспекты</h3>
        {aspects_html}
    </body>
    </html>
    """
    try:
        with open(pdf_path, "wb") as f: pisa.CreatePDF(html, dest=f)
        return pdf_path
    except: return None
