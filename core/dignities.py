"""Расчёт достоинств планет (афетика)"""

DIGNITIES = {
    'Sun': {'domicile': ['Leo'], 'exaltation': ['Ari'], 'detriment': ['Aqu'], 'fall': ['Lib']},
    'Moon': {'domicile': ['Cnc'], 'exaltation': ['Tau'], 'detriment': ['Cap'], 'fall': ['Sco']},
    'Mercury': {'domicile': ['Gem', 'Vir'], 'exaltation': ['Vir'], 'detriment': ['Sag', 'Pis'], 'fall': ['Pis']},
    'Venus': {'domicile': ['Tau', 'Lib'], 'exaltation': ['Pis'], 'detriment': ['Sco', 'Ari'], 'fall': ['Vir']},
    'Mars': {'domicile': ['Ari', 'Sco'], 'exaltation': ['Cap'], 'detriment': ['Lib', 'Tau'], 'fall': ['Cnc']},
    'Jupiter': {'domicile': ['Sag', 'Pis'], 'exaltation': ['Cnc'], 'detriment': ['Gem', 'Vir'], 'fall': ['Cap']},
    'Saturn': {'domicile': ['Cap', 'Aqu'], 'exaltation': ['Lib'], 'detriment': ['Cnc', 'Leo'], 'fall': ['Ari']},
    'Uranus': {'domicile': ['Aqu'], 'exaltation': ['Sco'], 'detriment': ['Leo'], 'fall': ['Tau']},
    'Neptune': {'domicile': ['Pis'], 'exaltation': ['Leo'], 'detriment': ['Vir'], 'fall': ['Aqu']},
    'Pluto': {'domicile': ['Sco'], 'exaltation': ['Ari'], 'detriment': ['Tau'], 'fall': ['Lib']}
}

DIGNITY_SCORES = {
    'domicile': 5,
    'exaltation': 4,
    'detriment': -5,
    'fall': -4
}

SIGN_ABBR = {
    'Овен': 'Ari', 'Телец': 'Tau', 'Близнецы': 'Gem', 'Рак': 'Cnc',
    'Лев': 'Leo', 'Дева': 'Vir', 'Весы': 'Lib', 'Скорпион': 'Sco',
    'Стрелец': 'Sag', 'Козерог': 'Cap', 'Водолей': 'Aqu', 'Рыбы': 'Pis'
}

DIGNITY_NAMES = {
    'domicile': 'Обитель',
    'exaltation': 'Экзальтация',
    'detriment': 'Изгнание',
    'fall': 'Падение'
}


def calculate_dignity(planet_key, sign_key):
    """Вычисляет достоинство планеты в знаке"""
    if planet_key not in DIGNITIES:
        return None, 0
    
    sign_abbr = SIGN_ABBR.get(sign_key, sign_key[:3])
    planet_dignities = DIGNITIES[planet_key]
    
    for dignity_type, signs in planet_dignities.items():
        if sign_abbr in signs:
            return DIGNITY_NAMES[dignity_type], DIGNITY_SCORES[dignity_type]
    
    return None, 0


def calculate_afetics(planets_data, aspects_list):
    """Расчёт афетических баллов"""
    afetics = {}
    
    for planet in planets_data:
        key = planet.get('key')
        if not key:
            continue
        
        score = planet.get('afetic_score', 0)
        dignity = planet.get('dignity', '')
        
        afetics[key] = {
            'name': planet.get('name', key),
            'score': score,
            'dignity': dignity
        }
    
    return afetics
