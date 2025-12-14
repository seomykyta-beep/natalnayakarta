"""Расчёт синастрии — совместимость двух людей"""


def calculate_synastry(chart1, chart2):
    """
    Рассчитывает совместимость двух натальных карт.
    
    chart1, chart2 — результаты build_chart() для двух людей
    
    Возвращает:
    - aspects: аспекты между планетами двух карт
    - score: общий балл совместимости (0-100)
    - interpretation: текстовая интерпретация
    """
    
    planets1 = {p['key']: p for p in chart1.get('planets', [])}
    planets2 = {p['key']: p for p in chart2.get('planets', [])}
    
    # Орбисы для синастрии (более широкие)
    ORBS = {
        'Conjunction': 10,
        'Opposition': 8,
        'Trine': 8,
        'Square': 7,
        'Sextile': 6,
    }
    
    ASPECTS = {
        0: ('Conjunction', 'Соединение'),
        60: ('Sextile', 'Секстиль'),
        90: ('Square', 'Квадрат'),
        120: ('Trine', 'Тригон'),
        180: ('Opposition', 'Оппозиция'),
    }
    
    # Веса для оценки совместимости
    WEIGHTS = {
        'Conjunction': {'positive': 8, 'negative': 4},  # Зависит от планет
        'Trine': {'positive': 10, 'negative': 0},
        'Sextile': {'positive': 7, 'negative': 0},
        'Square': {'positive': 0, 'negative': -6},
        'Opposition': {'positive': 3, 'negative': -4},
    }
    
    # Позитивные и негативные комбинации планет
    POSITIVE_COMBOS = {
        ('Sun', 'Moon'), ('Sun', 'Venus'), ('Moon', 'Venus'),
        ('Venus', 'Mars'), ('Sun', 'Jupiter'), ('Moon', 'Jupiter'),
        ('Venus', 'Jupiter'), ('Sun', 'ASC'), ('Moon', 'ASC'),
    }
    
    CHALLENGING_COMBOS = {
        ('Saturn', 'Sun'), ('Saturn', 'Moon'), ('Saturn', 'Venus'),
        ('Mars', 'Saturn'), ('Pluto', 'Venus'), ('Pluto', 'Moon'),
    }
    
    synastry_aspects = []
    total_score = 50  # Базовый балл
    
    main_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'ASC', 'MC']
    
    for key1 in main_planets:
        if key1 not in planets1:
            continue
        p1 = planets1[key1]
        pos1 = p1.get('abs_pos', 0)
        
        for key2 in main_planets:
            if key2 not in planets2:
                continue
            p2 = planets2[key2]
            pos2 = p2.get('abs_pos', 0)
            
            # Считаем расстояние
            diff = abs(pos1 - pos2)
            if diff > 180:
                diff = 360 - diff
            
            # Проверяем аспекты
            for exact_angle, (aspect_en, aspect_ru) in ASPECTS.items():
                orb = ORBS.get(aspect_en, 6)
                if abs(diff - exact_angle) <= orb:
                    actual_orb = abs(diff - exact_angle)
                    
                    # Определяем позитивность
                    combo = tuple(sorted([key1, key2]))
                    is_positive = combo in POSITIVE_COMBOS
                    is_challenging = combo in CHALLENGING_COMBOS
                    
                    # Считаем баллы
                    weight = WEIGHTS.get(aspect_en, {'positive': 0, 'negative': 0})
                    if is_positive:
                        score_delta = weight['positive'] * (1 - actual_orb / orb)
                    elif is_challenging:
                        score_delta = weight['negative'] * (1 - actual_orb / orb)
                    else:
                        # Нейтральные комбинации
                        score_delta = (weight['positive'] + weight['negative']) / 2 * (1 - actual_orb / orb)
                    
                    total_score += score_delta
                    
                    synastry_aspects.append({
                        'p1': p1.get('name', key1),
                        'p1_key': key1,
                        'p2': p2.get('name', key2),
                        'p2_key': key2,
                        'aspect': aspect_ru,
                        'aspect_en': aspect_en,
                        'orb': round(actual_orb, 1),
                        'is_positive': is_positive,
                        'is_challenging': is_challenging,
                        'score': round(score_delta, 1),
                    })
                    break
    
    # Нормализуем балл
    total_score = max(0, min(100, total_score))
    
    # Интерпретация
    if total_score >= 80:
        level = 'Отличная'
        description = 'Высокая гармония! Вы прекрасно понимаете друг друга, ваши энергии резонируют. Это может быть глубокая кармическая связь.'
    elif total_score >= 65:
        level = 'Хорошая'
        description = 'Хорошая совместимость с потенциалом для роста. Есть области для работы, но фундамент крепкий.'
    elif total_score >= 50:
        level = 'Средняя'
        description = 'Нормальная совместимость. Отношения потребуют усилий и компромиссов, но могут быть успешными при взаимном желании.'
    elif total_score >= 35:
        level = 'Сложная'
        description = 'Много напряжённых аспектов. Отношения будут требовать значительной работы и терпения с обеих сторон.'
    else:
        level = 'Очень сложная'
        description = 'Фундаментальные различия в энергиях. Такие отношения возможны, но потребуют огромных усилий.'
    
    # Сортируем аспекты по важности
    synastry_aspects.sort(key=lambda x: abs(x['score']), reverse=True)
    
    return {
        'score': round(total_score),
        'level': level,
        'description': description,
        'aspects': synastry_aspects[:15],  # Топ 15 аспектов
        'positive_count': len([a for a in synastry_aspects if a['is_positive']]),
        'challenging_count': len([a for a in synastry_aspects if a['is_challenging']]),
    }
