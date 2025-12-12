"""Модуль загрузки текстов из разбитых файлов"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEXTS_DIR = BASE_DIR / 'texts'

# Fallback на старый путь
if not TEXTS_DIR.exists():
    TEXTS_DIR = BASE_DIR / 'data' / 'texts'


def load_json(filename):
    """Загрузить JSON файл"""
    path = TEXTS_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# === ОСНОВНЫЕ РАЗДЕЛЫ ===
PLANETS_IN_SIGNS = load_json('planets_in_signs.json')
PLANETS_IN_HOUSES = load_json('planets_in_houses.json')
ASPECTS = load_json('aspects.json')

# === СПРАВОЧНИКИ ===
ELEMENTS = load_json('elements.json')
PLANETS = load_json('planets.json')
HOUSES = load_json('houses.json')
DIGNITIES = load_json('dignities.json')

# === ГРАДУСЫ ===
DEGREES_ALL = load_json('degrees_all.json')
DEGREES_ROYAL = load_json('degrees_royal.json')
DEGREES_DESTRUCTIVE = load_json('degrees_destructive.json')

# Объединённый словарь для совместимости
TEXTS = {
    'signs': PLANETS_IN_SIGNS,
    'houses': PLANETS_IN_HOUSES,
    'aspects': ASPECTS,
}


def get_text(category, planet_key, sub_key=None, gender='general'):
    """Получить текст по категории и ключу
    
    Args:
        category: 'signs' или 'houses' или 'aspects'
        planet_key: ключ планеты (Sun, Moon, etc)
        sub_key: знак/дом (Овен, House1) или None
        gender: 'general', 'male', 'female'
    """
    if category == 'signs':
        # Ключ: Sun_Овен
        key = f'{planet_key}_{sub_key}' if sub_key else planet_key
        data = PLANETS_IN_SIGNS.get(key, {})
    elif category == 'houses':
        # Ключ: Sun_House1
        key = f'{planet_key}_{sub_key}' if sub_key else planet_key
        data = PLANETS_IN_HOUSES.get(key, {})
    elif category == 'aspects':
        return ASPECTS.get(planet_key, {})
    else:
        return ''
    
    if isinstance(data, dict):
        return data.get(gender) or data.get('general', '')
    return str(data) if data else ''


def get_interpretation(planet_key, sign=None, gender='general'):
    """Получить интерпретацию планеты в знаке"""
    if sign:
        key = f'{planet_key}_{sign}'
        data = PLANETS_IN_SIGNS.get(key, {})
        if isinstance(data, dict):
            return data.get(gender) or data.get('general', '')
        return str(data) if data else ''
    return ''


def get_aspect_text(planet1, planet2, aspect_type):
    """Получить текст аспекта"""
    # Пробуем прямой порядок
    key = f'{planet1}_{planet2}'
    if key in ASPECTS:
        return ASPECTS[key].get(aspect_type, '')
    
    # Пробуем обратный порядок
    key = f'{planet2}_{planet1}'
    if key in ASPECTS:
        return ASPECTS[key].get(aspect_type, '')
    
    return ''


def get_planet_info(planet_key):
    """Получить информацию о планете"""
    return PLANETS.get(planet_key, {})


def get_house_info(house_num):
    """Получить информацию о доме"""
    return HOUSES.get(str(house_num), {})


def get_element_info(element):
    """Получить информацию о стихии"""
    return ELEMENTS.get(element, {})


def get_degree_info(abs_degree):
    """Получить информацию о градусе"""
    deg = str(int(abs_degree) + 1)
    
    if deg in DEGREES_ROYAL:
        return {'type': 'royal', **DEGREES_ROYAL[deg]}
    if deg in DEGREES_DESTRUCTIVE:
        return {'type': 'destructive', **DEGREES_DESTRUCTIVE[deg]}
    
    return DEGREES_ALL.get(deg, {})


def is_royal_degree(abs_degree):
    """Проверить королевский градус"""
    return str(int(abs_degree) + 1) in DEGREES_ROYAL


def is_destructive_degree(abs_degree):
    """Проверить разрушительный градус"""
    return str(int(abs_degree) + 1) in DEGREES_DESTRUCTIVE


# Функции сохранения
def save_json(filename, data):
    path = TEXTS_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_planets_in_signs(data):
    save_json('planets_in_signs.json', data)


def save_planets_in_houses(data):
    save_json('planets_in_houses.json', data)


def save_aspects(data):
    save_json('aspects.json', data)
