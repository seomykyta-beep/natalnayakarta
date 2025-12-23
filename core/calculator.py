"""Основной калькулятор натальной карты"""
import math
from datetime import datetime
from pathlib import Path
import pytz

from skyfield.api import load

from .constants import ZODIAC_SIGNS, ZODIAC_ICONS, PLANET_NAMES, PLANET_ICONS, ZODIAC_SIGNS_LOCATIVE
from .texts import TEXTS, get_text, get_interpretation
from .aspects import find_aspects, find_transit_aspects
from .houses import calculate_houses, get_house_placement
from .dignities import calculate_dignity, calculate_afetics

# Загрузка эфемерид
BASE_DIR = Path(__file__).parent.parent
EPHEMERIS_FILE = str(BASE_DIR / 'data' / 'de421.bsp')

SKYFIELD_AVAILABLE = False
try:
    planets = load(EPHEMERIS_FILE)
    ts = load.timescale()
    earth = planets['earth']
    moon = planets['moon']
    SKYFIELD_AVAILABLE = True
except Exception as e:
    print(f'Error loading ephemeris: {e}')


def degrees_to_zodiac(lon):
    """Преобразует долготу в знак зодиака"""
    lon = lon % 360
    sign_num = int(lon // 30)
    degree = lon % 30
    return ZODIAC_SIGNS[sign_num], degree, ZODIAC_ICONS[sign_num]


def get_city_info(city_name, lat=None, lon=None):
    """Возвращает координаты и часовой пояс города"""
    cities = {
        'Moscow': (55.75, 37.61, 'Europe/Moscow'),
        'Москва': (55.75, 37.61, 'Europe/Moscow'),
        'Saint Petersburg': (59.93, 30.31, 'Europe/Moscow'),
        'Санкт-Петербург': (59.93, 30.31, 'Europe/Moscow'),
        'Surgut': (61.25, 73.42, 'Asia/Yekaterinburg'),
        'Сургут': (61.25, 73.42, 'Asia/Yekaterinburg'),
    }
    
    if lat and lon:
        return lat, lon, 'Europe/Moscow'
    
    city_data = cities.get(city_name)
    if city_data:
        return city_data
    
    return 55.75, 37.61, 'Europe/Moscow'


def build_chart(local_dt, latitude, longitude, city_label, gender='male'):
    """Строит натальную карту"""
    utc_dt = local_dt.astimezone(pytz.UTC)
    t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
    
    # observer removed - не нужен для расчётов
    
    planets_data = []
    planet_bodies = [
        ('sun', 'Sun'), ('moon', 'Moon'), ('mercury', 'Mercury'),
        ('venus', 'Venus'), ('mars', 'Mars'), ('jupiter barycenter', 'Jupiter'),
        ('saturn barycenter', 'Saturn'), ('uranus barycenter', 'Uranus'),
        ('neptune barycenter', 'Neptune'), ('pluto barycenter', 'Pluto')
    ]
    
    houses = calculate_houses(t, latitude, longitude)
    
    for body_name, key in planet_bodies:
        try:
            body = planets[body_name]
            astrometric = earth.at(t).observe(body)
            apparent = astrometric.apparent()
            
            lat_ecl, lon_ecl, _ = apparent.ecliptic_latlon()
            lon = lon_ecl.degrees
            
            sign, deg, icon = degrees_to_zodiac(lon)
            house = get_house_placement(lon, houses)
            
            dignity, afetic_score = calculate_dignity(key, sign)
            
            text_sign = get_interpretation(key, sign, gender)
            text_house = get_text('houses', key, f'House{house}', gender)
            
            planets_data.append({
                'name': PLANET_NAMES.get(body_name, key),
                'key': key,
                'icon': PLANET_ICONS.get(body_name, ''),
                'sign': sign,
                'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
                'sign_icon': icon,
                'degree': round(deg, 2),
                'abs_pos': round(lon, 2),
                'house': house,
                'retrograde': False,
                'dignity': dignity or '',
                'afetic_score': afetic_score,
                'text': f'{text_sign}\n{text_house}'
            })
        except Exception as e:
            print(f'Error calculating {body_name}: {e}')
    
    # Расчёт узлов и Лилит
    jd = t.tt
    mean_node = (125.04 - 0.0529539 * (jd - 2451545.0)) % 360
    sign, deg, icon = degrees_to_zodiac(mean_node)
    house = get_house_placement(mean_node, houses)
    
    planets_data.append({
        'name': 'Северный Узел',
        'key': 'North_node',
        'icon': '☊',
        'sign': sign,
        'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
        'sign_icon': icon,
        'degree': round(deg, 2),
        'abs_pos': round(mean_node, 2),
        'house': house,
        'retrograde': True,
        'dignity': '',
        'afetic_score': 0,
        'text': ((get_interpretation('North_node', sign, gender, mode='natal') + '\n' + get_text('houses', 'North_node', f'House{house}', gender, mode='natal')).strip() or 'Кармическая задача')
    })
    
    south_node = (mean_node + 180) % 360
    sign, deg, icon = degrees_to_zodiac(south_node)
    house = get_house_placement(south_node, houses)
    
    planets_data.append({
        'name': 'Южный Узел',
        'key': 'South_node',
        'icon': '☋',
        'sign': sign,
        'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
        'sign_icon': icon,
        'degree': round(deg, 2),
        'abs_pos': round(south_node, 2),
        'house': house,
        'retrograde': True,
        'dignity': '',
        'afetic_score': 0,
        'text': ((get_interpretation('South_node', sign, gender, mode='natal') + '\n' + get_text('houses', 'South_node', f'House{house}', gender, mode='natal')).strip() or 'Прошлый опыт')
    })
    
    lilith = (mean_node + 90) % 360
    sign, deg, icon = degrees_to_zodiac(lilith)
    house = get_house_placement(lilith, houses)
    
    planets_data.append({
        'name': 'Лилит',
        'key': 'Lilith',
        'icon': '⚸',
        'sign': sign,
        'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
        'sign_icon': icon,
        'degree': round(deg, 2),
        'abs_pos': round(lilith, 2),
        'house': house,
        'retrograde': False,
        'dignity': '',
        'afetic_score': 0,
        'text': ((get_interpretation('Lilith', sign, gender, mode='natal') + '\n' + get_text('houses', 'Lilith', f'House{house}', gender, mode='natal')).strip() or 'Теневая сторона')
    })
    
    # ASC и MC
    asc = houses[0]
    sign, deg, icon = degrees_to_zodiac(asc)
    planets_data.append({
        'name': 'Асцендент',
        'key': 'ASC',
        'icon': '⬆️',
        'sign': sign,
        'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
        'sign_icon': icon,
        'degree': round(deg, 2),
        'abs_pos': round(asc, 2),
        'house': 'ASC',
        'retrograde': False,
        'dignity': '',
        'afetic_score': 0,
        'text': (f"Асцендент в {ZODIAC_SIGNS_LOCATIVE.get(sign, sign)} описывает ваш стиль проявления и первое впечатление. Это то, как вы входите в контакт с миром: темп, манера речи, пластика, границы.\n\nВ плюсе это дает ясный образ и уверенное самопредъявление; в минусе - игру в роль и зависимость от реакции. Полезно время от времени спрашивать себя: какой образ я транслирую и совпадает ли он с тем, что мне важно?\n\nПрактика: меньше доказывать, больше показывать через действия. Выбирайте один маленький жест (тон, поза, слово), который делает вас спокойнее и собраннее - и закрепляйте его.")
    })
    
    mc = houses[9]
    sign, deg, icon = degrees_to_zodiac(mc)
    planets_data.append({
        'name': 'Середина Неба',
        'key': 'MC',
        'icon': 'M',
        'sign': sign,
        'sign_locative': ZODIAC_SIGNS_LOCATIVE.get(sign, sign),
        'sign_icon': icon,
        'degree': round(deg, 2),
        'abs_pos': round(mc, 2),
        'house': 'MC',
        'retrograde': False,
        'dignity': '',
        'afetic_score': 0,
        'text': (f"Середина Неба в {ZODIAC_SIGNS_LOCATIVE.get(sign, sign)} показывает ваш вектор карьеры и репутации: за что вас узнают, где вы хотите быть полезным(ой), какой стиль ответственности для вас естественен.\n\nВ плюсе МС дает понятный профессиональный маршрут и способность собирать результаты; в минусе - страх оценки и жесткую зависимость от статуса. Важно строить путь не из тревоги, а из смысла.\n\nПрактика: сформулируйте одну долгую цель и разложите ее на квартальные шаги. Тогда МС раскрывается как опора: вы видите, что делать сегодня, и не теряете направление.")
    })
    
    aspects = find_aspects(planets_data)
    afetics = calculate_afetics(planets_data, aspects)
    
    meta = {
        'city': city_label,
        'coords': f'{latitude:.2f}, {longitude:.2f}',
        'dt': local_dt.strftime('%d.%m.%Y %H:%M')
    }
    
    return {
        'planets': planets_data,
        'houses': houses,
        'aspects': aspects,
        'meta': meta,
        'afetics': afetics
    }


def calculate_real_chart(name, year, month, day, hour, minute, city,
                        lat=None, lon=None,
                        transit_year=None, transit_month=None, transit_day=None,
                        transit_hour=None, transit_minute=None,
                        transit_city=None, transit_lat=None, transit_lon=None,
                        custom_orbs=None, gender='male'):
    """Расчёт натальной карты с транзитами"""
    if not SKYFIELD_AVAILABLE:
        return {'error': 'Ephemeris not loaded'}
    
    r_lat, r_lon, tz_str = get_city_info(city, lat, lon)
    tz = pytz.timezone(tz_str)
    natal_dt = tz.localize(datetime(year, month, day, hour, minute))
    natal_chart = build_chart(natal_dt, r_lat, r_lon, city, gender=gender)
    
    if custom_orbs:
        natal_chart['aspects'] = find_aspects(natal_chart['planets'], custom_orbs)
    
    result = {
        'name': name,
        'gender': gender,
        'planets': natal_chart['planets'],
        'houses': natal_chart['houses'],
        'aspects': natal_chart['aspects'],
        'meta': natal_chart['meta'],
        'afetics': natal_chart.get('afetics', {})
    }
    
    if transit_year and transit_month and transit_day:
        t_city = transit_city or city
        t_lat, t_lon, t_tz_str = get_city_info(t_city, transit_lat or lat, transit_lon or lon)
        t_tz = pytz.timezone(t_tz_str)
        transit_dt = t_tz.localize(datetime(
            transit_year, transit_month, transit_day,
            transit_hour or 12, transit_minute or 0
        ))
        transit_chart = build_chart(transit_dt, t_lat, t_lon, t_city)
        
        result['transit_planets'] = transit_chart['planets']
        result['transit_aspects'] = find_transit_aspects(
            natal_chart['planets'],
            transit_chart['planets'],
            custom_orbs
        )
        result['transit_meta'] = transit_chart['meta']
    
    return result


def calculate_chart_with_mode(name, year, month, day, hour, minute, city,
                              lat=None, lon=None, gender='male', mode='natal',
                              transit_year=None, transit_month=None, transit_day=None,
                              transit_hour=None, transit_minute=None,
                              transit_city=None, transit_lat=None, transit_lon=None,
                              solar_year=None, solar_city=None, solar_lat=None, solar_lon=None,
                              lunar_year=None, lunar_month=None, lunar_city=None, lunar_lat=None, lunar_lon=None,
                              custom_orbs=None):
    """Универсальный расчёт карты для всех режимов"""
    
    result = calculate_real_chart(
        name, year, month, day, hour, minute, city,
        lat, lon,
        transit_year, transit_month, transit_day,
        transit_hour, transit_minute,
        transit_city, transit_lat, transit_lon,
        custom_orbs, gender
    )
    
    result['mode'] = mode
    
    if mode == 'solar' and solar_year:
        from .solar import find_solar_return
        
        r_lat, r_lon, tz_str = get_city_info(solar_city or city, solar_lat or lat, solar_lon or lon)
        natal_sun = next((p for p in result['planets'] if p['key'] == 'Sun'), None)
        
        if natal_sun:
            solar_data = find_solar_return(
                natal_sun['abs_pos'],
                solar_year,
                r_lat, r_lon, tz_str,
                month, day
            )
            result['solar'] = solar_data
    
    elif mode == 'lunar' and lunar_year and lunar_month:
        from .lunar import find_lunar_return
        
        r_lat, r_lon, tz_str = get_city_info(lunar_city or city, lunar_lat or lat, lunar_lon or lon)
        natal_moon = next((p for p in result['planets'] if p['key'] == 'Moon'), None)
        
        if natal_moon:
            lunar_data = find_lunar_return(
                natal_moon['abs_pos'],
                lunar_year, lunar_month,
                r_lat, r_lon, tz_str
            )
            result['lunar'] = lunar_data
    
    return result
