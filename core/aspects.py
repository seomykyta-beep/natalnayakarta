"""Расчёт аспектов между планетами"""
from .constants import DEFAULT_ORBS
from .texts import TEXTS

ASPECTS = {
    0: {'name': 'Соединение', 'orb': 8, 'type': 'Conjunction'},
    60: {'name': 'Секстиль', 'orb': 6, 'type': 'Sextile'},
    90: {'name': 'Квадрат', 'orb': 8, 'type': 'Square'},
    120: {'name': 'Тригон', 'orb': 8, 'type': 'Trine'},
    150: {'name': 'Квинконс', 'orb': 4, 'type': 'Quincunx'},
    180: {'name': 'Оппозиция', 'orb': 8, 'type': 'Opposition'}
}

ASPECT_TYPE_MAP = {
    'Conjunction': 'Соединение',
    'Sextile': 'Секстиль',
    'Square': 'Квадрат',
    'Trine': 'Тригон',
    'Quincunx': 'Квинконс',
    'Opposition': 'Оппозиция',
}


def get_aspect_text_key(aspect_type_en):
    """Переводит тип аспекта на русский"""
    return ASPECT_TYPE_MAP.get(aspect_type_en, aspect_type_en)


def find_aspects(planets_data, custom_orbs=None):
    """Находит аспекты между планетами"""
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
                    p1_key = p1.get('key', '')
                    p2_key = p2.get('key', '')
                    aspect_key = f'{p1_key}_{p2_key}'
                    aspect_key_rev = f'{p2_key}_{p1_key}'
                    aspect_text_key = get_aspect_text_key(data['type'])
                    
                    aspects_data = TEXTS.get('aspects', {})
                    aspect_text_raw = aspects_data.get(aspect_key, aspects_data.get(aspect_key_rev, {})).get(aspect_text_key, '')
                    
                    if isinstance(aspect_text_raw, dict):
                        aspect_text = aspect_text_raw.get('text', '')
                    else:
                        aspect_text = aspect_text_raw
                    
                    if not aspect_text:
                        aspect_text = f"Аспект {data['name']} между {p1['name']} и {p2['name']} ({round(diff,1)}°)"
                    
                    aspects_list.append({
                        'p1': p1['name'],
                        'p2': p2['name'],
                        'p1_key': p1_key,
                        'p2_key': p2_key,
                        'type': data['type'],
                        'name': data['name'],
                        'orb': round(abs(diff - angle), 2),
                        'exact_orb': round(diff, 2),
                        'text': aspect_text
                    })
    
    return aspects_list


def find_transit_aspects(natal_planets, transit_planets, custom_orbs=None):
    """Находит аспекты между натальными и транзитными планетами"""
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
                    aspects_list.append({
                        'natal': p1['name'],
                        'transit': p2['name'],
                        'p1_key': p1.get('key'),
                        'p2_key': p2.get('key'),
                        'type': data['type'],
                        'name': data['name'],
                        'orb': round(abs(diff - angle), 2),
                        'text': ''
                    })
    
    return aspects_list
