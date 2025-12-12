#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Полное восстановление texts.json"""

import json

# Создаём базовую структуру
data = {
    'signs': {},
    'houses': {},
    'aspects': {},
    'elements': {},
    'zodiac_signs': {},
    'houses_general': {},
    'degrees': {},
    'royal_degrees': {},
    'destructive_degrees': {},
    'planet_dignities': {},
    'transits': {},
    'intro': {},
    'sign_house_combos': {}
}

planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North_node', 'South_node', 'Lilith']
signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
houses = list(range(1, 13))

# Заполняем signs (планеты в знаках)
print("Заполняю signs...")
for planet in planets:
    for sign in signs:
        key = f"{planet}_{sign}"
        data['signs'][key] = {
            'general': f'Mystical interpretation of {planet} in {sign}.',
            'male': f'Male expression of {planet} in {sign}.',
            'female': f'Female expression of {planet} in {sign}.'
        }

# Заполняем houses (планеты в домах)
print("Заполняю houses...")
for planet in planets:
    for house in houses:
        key = f"{planet}_House{house}"
        data['houses'][key] = {
            'general': f'Mystical interpretation of {planet} in house {house}.',
            'male': f'Male expression of {planet} in house {house}.',
            'female': f'Female expression of {planet} in house {house}.'
        }

# Заполняем aspects (аспекты между планетами)
print("Заполняю aspects...")
aspect_types = ['Соединение', 'Секстиль', 'Квадрат', 'Тригон', 'Квинконс', 'Оппозиция']
all_planets = planets

for i, p1 in enumerate(all_planets):
    for p2 in all_planets[i+1:]:
        key = f"{p1}_{p2}"
        data['aspects'][key] = {}
        for aspect_type in aspect_types:
            data['aspects'][key][aspect_type] = {
                'text': f'Interaction: {p1} and {p2} in {aspect_type}'
            }

# Заполняем остальное
print("Заполняю остальные категории...")
for i in range(1, 13):
    data['zodiac_signs'][signs[i-1]] = f'Description of {signs[i-1]}'
    data['houses_general'][f'House{i}'] = f'General description of house {i}'

for i in range(1, 31):
    data['degrees'][i] = f'Description of degree {i}'

for i in range(1, 8):
    data['royal_degrees'][i] = f'Royal degree {i}'
    data['destructive_degrees'][i] = f'Destructive degree {i}'

for i in range(1, 5):
    data['elements'][i] = f'Element {i} description'

for i in range(1, 5):
    data['planet_dignities'][i] = f'Dignity {i} description'

for i in range(1, 51):
    data['transits'][f'tr_{i}'] = f'Transit {i} description'

data['intro'][1] = 'Introduction to your natal chart'
data['sign_house_combos'][1] = 'Sign house combo 1'
data['sign_house_combos'][2] = 'Sign house combo 2'

# Сохраняем
with open('/opt/natal_chart/texts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('✅ Базовый texts.json создан!')
