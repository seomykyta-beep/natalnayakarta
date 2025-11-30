#!/usr/bin/env python3
"""
Скрипт для перевода ключей аспектов на русский язык
"""
import json

# Словарь перевода аспектов
ASPECT_TRANSLATION = {
    "Conjunction": "Соединение",
    "Sextile": "Секстиль", 
    "Square": "Квадрат",
    "Trine": "Тригон",
    "Opposition": "Оппозиция"
}

# Словарь перевода планет
PLANET_TRANSLATION = {
    "Sun": "Солнце",
    "Moon": "Луна",
    "Mercury": "Меркурий",
    "Venus": "Венера",
    "Mars": "Марс",
    "Jupiter": "Юпитер",
    "Saturn": "Сатурн",
    "Uranus": "Уран",
    "Neptune": "Нептун",
    "Pluto": "Плутон",
    "North_node": "Сев_Узел",
    "South_node": "Юж_Узел",
    "Lilith": "Лилит"
}

def translate_aspects():
    # Загружаем texts.json
    with open("texts.json", "r", encoding="utf-8") as f:
        texts = json.load(f)
    
    # Переводим аспекты
    old_aspects = texts.get("aspects", {})
    new_aspects = {}
    
    for pair_key, aspect_dict in old_aspects.items():
        # Переводим ключ пары (Sun_Moon -> Солнце_Луна)
        parts = pair_key.split("_")
        if len(parts) == 2:
            p1, p2 = parts
            new_pair_key = f"{PLANET_TRANSLATION.get(p1, p1)}_{PLANET_TRANSLATION.get(p2, p2)}"
        elif len(parts) == 3:  # North_node, South_node
            p1 = parts[0]
            p2 = "_".join(parts[1:])
            new_pair_key = f"{PLANET_TRANSLATION.get(p1, p1)}_{PLANET_TRANSLATION.get(p2, p2)}"
        elif len(parts) == 4:  # North_node_South_node
            p1 = "_".join(parts[:2])
            p2 = "_".join(parts[2:])
            new_pair_key = f"{PLANET_TRANSLATION.get(p1, p1)}_{PLANET_TRANSLATION.get(p2, p2)}"
        else:
            new_pair_key = pair_key
        
        # Переводим ключи аспектов
        new_aspect_dict = {}
        for aspect_key, text in aspect_dict.items():
            new_aspect_key = ASPECT_TRANSLATION.get(aspect_key, aspect_key)
            new_aspect_dict[new_aspect_key] = text
        
        new_aspects[new_pair_key] = new_aspect_dict
    
    texts["aspects"] = new_aspects
    
    # Сохраняем
    with open("texts.json", "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)
    
    print("✅ Аспекты переведены на русский!")
    print(f"Всего пар планет: {len(new_aspects)}")
    print(f"Пример ключей: {list(new_aspects.keys())[:5]}")
    print(f"Пример аспектов: {list(list(new_aspects.values())[0].keys())}")

if __name__ == "__main__":
    translate_aspects()


