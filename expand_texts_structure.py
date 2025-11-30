#!/usr/bin/env python3
"""
Скрипт для расширения структуры texts.json
Добавляет новые разделы для админки
"""
import json

# Знаки зодиака
SIGNS = {
    "Ari": "Овен", "Tau": "Телец", "Gem": "Близнецы", "Cnc": "Рак",
    "Leo": "Лев", "Vir": "Дева", "Lib": "Весы", "Sco": "Скорпион",
    "Sag": "Стрелец", "Cap": "Козерог", "Aqu": "Водолей", "Pis": "Рыбы"
}

# Планеты
PLANETS = {
    "Sun": "Солнце", "Moon": "Луна", "Mercury": "Меркурий", "Venus": "Венера",
    "Mars": "Марс", "Jupiter": "Юпитер", "Saturn": "Сатурн", "Uranus": "Уран",
    "Neptune": "Нептун", "Pluto": "Плутон", "North_node": "Сев.Узел", 
    "South_node": "Юж.Узел", "Lilith": "Лилит"
}

# Стихии
ELEMENTS = {
    "fire": {"name": "Огонь", "signs": ["Ari", "Leo", "Sag"]},
    "earth": {"name": "Земля", "signs": ["Tau", "Vir", "Cap"]},
    "air": {"name": "Воздух", "signs": ["Gem", "Lib", "Aqu"]},
    "water": {"name": "Вода", "signs": ["Cnc", "Sco", "Pis"]}
}

# Королевские градусы
ROYAL_DEGREES = {
    "Ari_18": "18° Овна",
    "Gem_9": "9° Близнецов", 
    "Leo_7": "7° Льва",
    "Vir_25": "25° Девы",
    "Sco_13": "13° Скорпиона",
    "Cap_11": "11° Козерога",
    "Aqu_30": "30° Водолея"
}

# Разрушительные градусы
DESTRUCTIVE_DEGREES = {
    "Ari_23": "23° Овна",
    "Gem_13": "13° Близнецов",
    "Leo_10": "10° Льва",
    "Lib_1": "1° Весов",
    "Sco_19": "19° Скорпиона",
    "Cap_19": "19° Козерога",
    "Pis_4": "4° Рыб"
}

# Таблица достоинств планет (обитель, экзальтация, изгнание, падение)
PLANET_DIGNITIES = {
    "Sun": {"domicile": ["Leo"], "exaltation": ["Ari"], "detriment": ["Aqu"], "fall": ["Lib"]},
    "Moon": {"domicile": ["Cnc"], "exaltation": ["Tau"], "detriment": ["Cap"], "fall": ["Sco"]},
    "Mercury": {"domicile": ["Gem", "Vir"], "exaltation": ["Vir"], "detriment": ["Sag", "Pis"], "fall": ["Pis"]},
    "Venus": {"domicile": ["Tau", "Lib"], "exaltation": ["Pis"], "detriment": ["Ari", "Sco"], "fall": ["Vir"]},
    "Mars": {"domicile": ["Ari", "Sco"], "exaltation": ["Cap"], "detriment": ["Tau", "Lib"], "fall": ["Cnc"]},
    "Jupiter": {"domicile": ["Sag", "Pis"], "exaltation": ["Cnc"], "detriment": ["Gem", "Vir"], "fall": ["Cap"]},
    "Saturn": {"domicile": ["Cap", "Aqu"], "exaltation": ["Lib"], "detriment": ["Cnc", "Leo"], "fall": ["Ari"]},
    "Uranus": {"domicile": ["Aqu"], "exaltation": ["Sco"], "detriment": ["Leo"], "fall": ["Tau"]},
    "Neptune": {"domicile": ["Pis"], "exaltation": ["Cnc"], "detriment": ["Vir"], "fall": ["Cap"]},
    "Pluto": {"domicile": ["Sco"], "exaltation": ["Leo"], "detriment": ["Tau"], "fall": ["Aqu"]}
}

def expand_structure():
    # Загружаем существующий texts.json
    with open("texts.json", "r", encoding="utf-8") as f:
        texts = json.load(f)
    
    # 1. Добавляем раздел "Стихии"
    if "elements" not in texts:
        texts["elements"] = {}
        for elem_key, elem_data in ELEMENTS.items():
            texts["elements"][elem_key] = {
                "name": elem_data["name"],
                "signs": elem_data["signs"],
                "description": f"Описание стихии {elem_data['name']} (ЗАПОЛНИТЬ)",
                "description_male": f"Описание стихии {elem_data['name']} для мужчины (ЗАПОЛНИТЬ)",
                "description_female": f"Описание стихии {elem_data['name']} для женщины (ЗАПОЛНИТЬ)"
            }
        print("✅ Добавлен раздел 'Стихии'")
    
    # 2. Добавляем раздел "Знаки зодиака" (отдельно)
    if "zodiac_signs" not in texts:
        texts["zodiac_signs"] = {}
        for sign_key, sign_name in SIGNS.items():
            texts["zodiac_signs"][sign_key] = {
                "name": sign_name,
                "description": f"Описание знака {sign_name} (ЗАПОЛНИТЬ)",
                "description_male": f"Описание знака {sign_name} для мужчины (ЗАПОЛНИТЬ)",
                "description_female": f"Описание знака {sign_name} для женщины (ЗАПОЛНИТЬ)"
            }
        print("✅ Добавлен раздел 'Знаки зодиака'")
    
    # 3. Добавляем раздел "Дома" (отдельно)
    if "houses_general" not in texts:
        texts["houses_general"] = {}
        for i in range(1, 13):
            texts["houses_general"][str(i)] = {
                "name": f"{i} дом",
                "description": f"Описание {i} дома (ЗАПОЛНИТЬ)",
                "description_male": f"Описание {i} дома для мужчины (ЗАПОЛНИТЬ)",
                "description_female": f"Описание {i} дома для женщины (ЗАПОЛНИТЬ)"
            }
        print("✅ Добавлен раздел 'Дома (общие)'")
    
    # 4. Добавляем раздел "Градусы" (1-30 для каждого знака)
    if "degrees" not in texts:
        texts["degrees"] = {}
        for sign_key, sign_name in SIGNS.items():
            texts["degrees"][sign_key] = {}
            for deg in range(1, 31):
                texts["degrees"][sign_key][str(deg)] = {
                    "description": f"{deg}° {sign_name} (ЗАПОЛНИТЬ)"
                }
        print("✅ Добавлен раздел 'Градусы' (360 градусов)")
    
    # 5. Добавляем раздел "Королевские градусы"
    if "royal_degrees" not in texts:
        texts["royal_degrees"] = {}
        for deg_key, deg_name in ROYAL_DEGREES.items():
            texts["royal_degrees"][deg_key] = {
                "name": deg_name,
                "description": f"Королевский градус {deg_name} (ЗАПОЛНИТЬ)"
            }
        print("✅ Добавлен раздел 'Королевские градусы'")
    
    # 6. Добавляем раздел "Разрушительные градусы"
    if "destructive_degrees" not in texts:
        texts["destructive_degrees"] = {}
        for deg_key, deg_name in DESTRUCTIVE_DEGREES.items():
            texts["destructive_degrees"][deg_key] = {
                "name": deg_name,
                "description": f"Разрушительный градус {deg_name} (ЗАПОЛНИТЬ)"
            }
        print("✅ Добавлен раздел 'Разрушительные градусы'")
    
    # 7. Добавляем раздел "Состояние планет" (обитель, экзальтация, изгнание, падение)
    if "planet_dignities" not in texts:
        texts["planet_dignities"] = {
            "domicile": {},    # Обитель
            "exaltation": {},  # Экзальтация
            "detriment": {},   # Изгнание
            "fall": {}         # Падение
        }
        
        for planet_key, dignities in PLANET_DIGNITIES.items():
            planet_name = PLANETS[planet_key]
            
            # Обитель
            for sign in dignities["domicile"]:
                key = f"{planet_key}_{sign}"
                sign_name = SIGNS[sign]
                texts["planet_dignities"]["domicile"][key] = {
                    "planet": planet_name,
                    "sign": sign_name,
                    "description": f"{planet_name} в обители ({sign_name}): Планета проявляется наиболее естественно и гармонично.",
                    "description_male": f"{planet_name} в обители ({sign_name}) у мужчины (ЗАПОЛНИТЬ)",
                    "description_female": f"{planet_name} в обители ({sign_name}) у женщины (ЗАПОЛНИТЬ)"
                }
            
            # Экзальтация
            for sign in dignities["exaltation"]:
                key = f"{planet_key}_{sign}"
                sign_name = SIGNS[sign]
                texts["planet_dignities"]["exaltation"][key] = {
                    "planet": planet_name,
                    "sign": sign_name,
                    "description": f"{planet_name} в экзальтации ({sign_name}): Планета проявляется с максимальной силой и яркостью.",
                    "description_male": f"{planet_name} в экзальтации ({sign_name}) у мужчины (ЗАПОЛНИТЬ)",
                    "description_female": f"{planet_name} в экзальтации ({sign_name}) у женщины (ЗАПОЛНИТЬ)"
                }
            
            # Изгнание
            for sign in dignities["detriment"]:
                key = f"{planet_key}_{sign}"
                sign_name = SIGNS[sign]
                texts["planet_dignities"]["detriment"][key] = {
                    "planet": planet_name,
                    "sign": sign_name,
                    "description": f"{planet_name} в изгнании ({sign_name}): Планете сложно проявляться, требуется работа над собой.",
                    "description_male": f"{planet_name} в изгнании ({sign_name}) у мужчины (ЗАПОЛНИТЬ)",
                    "description_female": f"{planet_name} в изгнании ({sign_name}) у женщины (ЗАПОЛНИТЬ)"
                }
            
            # Падение
            for sign in dignities["fall"]:
                key = f"{planet_key}_{sign}"
                sign_name = SIGNS[sign]
                texts["planet_dignities"]["fall"][key] = {
                    "planet": planet_name,
                    "sign": sign_name,
                    "description": f"{planet_name} в падении ({sign_name}): Планета ослаблена, но несет кармические уроки.",
                    "description_male": f"{planet_name} в падении ({sign_name}) у мужчины (ЗАПОЛНИТЬ)",
                    "description_female": f"{planet_name} в падении ({sign_name}) у женщины (ЗАПОЛНИТЬ)"
                }
        
        print("✅ Добавлен раздел 'Состояние планет'")
    
    # 8. Расширяем раздел "signs" - добавляем разделение по полу
    if "signs" in texts:
        for planet_key in texts["signs"]:
            for sign_key in texts["signs"][planet_key]:
                current_text = texts["signs"][planet_key][sign_key]
                if isinstance(current_text, str):
                    # Преобразуем в словарь с разделением по полу
                    texts["signs"][planet_key][sign_key] = {
                        "general": current_text,
                        "male": f"(Для мужчины) {current_text[:100]}... (ДОПОЛНИТЬ)",
                        "female": f"(Для женщины) {current_text[:100]}... (ДОПОЛНИТЬ)"
                    }
        print("✅ Раздел 'Планеты в знаках' расширен (добавлен пол)")
    
    # 9. Расширяем раздел "houses" - добавляем разделение по полу
    if "houses" in texts:
        for planet_key in texts["houses"]:
            for house_key in texts["houses"][planet_key]:
                current_text = texts["houses"][planet_key][house_key]
                if isinstance(current_text, str):
                    texts["houses"][planet_key][house_key] = {
                        "general": current_text,
                        "male": f"(Для мужчины) {current_text[:80]}... (ДОПОЛНИТЬ)",
                        "female": f"(Для женщины) {current_text[:80]}... (ДОПОЛНИТЬ)"
                    }
        print("✅ Раздел 'Планеты в домах' расширен (добавлен пол)")
    
    # 10. Добавляем раздел "Планета в знаке в доме" (комбинации)
    if "sign_house_combos" not in texts:
        texts["sign_house_combos"] = {}
        # Создаем структуру, но НЕ заполняем все 1728+ комбинаций сразу
        # Это будет заполняться через админку
        texts["sign_house_combos"]["_info"] = "Комбинации: Планета в Знаке в Доме. Заполняется через админку."
        texts["sign_house_combos"]["_example"] = {
            "Sun_Ari_1": {
                "general": "Солнце в Овне в 1 доме: ...",
                "male": "Солнце в Овне в 1 доме (мужчина): ...",
                "female": "Солнце в Овне в 1 доме (женщина): ..."
            }
        }
        print("✅ Добавлен раздел 'Комбинации планета-знак-дом' (структура)")
    
    # Сохраняем
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*50)
    print("✅ Структура texts.json расширена!")
    print("="*50)
    print("\nНовые разделы:")
    print("- elements (Стихии)")
    print("- zodiac_signs (Знаки зодиака отдельно)")
    print("- houses_general (Дома отдельно)")
    print("- degrees (Градусы 1-30 для каждого знака)")
    print("- royal_degrees (Королевские градусы)")
    print("- destructive_degrees (Разрушительные градусы)")
    print("- planet_dignities (Обитель/Экзальтация/Изгнание/Падение)")
    print("- sign_house_combos (Комбинации планета-знак-дом)")
    print("\nСуществующие разделы расширены:")
    print("- signs (добавлен пол: general/male/female)")
    print("- houses (добавлен пол: general/male/female)")

if __name__ == "__main__":
    expand_structure()


