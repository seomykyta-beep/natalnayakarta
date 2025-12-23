# Расчёт аспектов между планетами
from .constants import DEFAULT_ORBS
from .texts import get_db_aspect_text

ASPECTS = {
    0: {"name": "Соединение", "orb": 8, "type": "Conjunction"},
    60: {"name": "Секстиль", "orb": 6, "type": "Sextile"},
    90: {"name": "Квадрат", "orb": 8, "type": "Square"},
    120: {"name": "Тригон", "orb": 8, "type": "Trine"},
    150: {"name": "Квинконс", "orb": 4, "type": "Quincunx"},
    180: {"name": "Оппозиция", "orb": 8, "type": "Opposition"},
}

ASPECT_TYPE_MAP = {
    "Conjunction": "Соединение",
    "Sextile": "Секстиль",
    "Square": "Квадрат",
    "Trine": "Тригон",
    "Quincunx": "Квинконс",
    "Opposition": "Оппозиция",
}


def get_aspect_text_key(aspect_type_en):
    return ASPECT_TYPE_MAP.get(aspect_type_en, aspect_type_en)


def find_aspects(planets_data, custom_orbs=None):
    orbs = DEFAULT_ORBS.copy()
    if custom_orbs:
        orbs.update(custom_orbs)

    aspects_list = []

    for i in range(len(planets_data)):
        for j in range(i + 1, len(planets_data)):
            p1 = planets_data[i]
            p2 = planets_data[j]

            diff = abs(p1["abs_pos"] - p2["abs_pos"])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                orb = orbs.get(angle, data["orb"])
                if abs(diff - angle) <= orb:
                    p1_key = p1.get("key", "")
                    p2_key = p2.get("key", "")

                    aspect_text = get_db_aspect_text(p1_key, p2_key, data["type"], mode="natal")
                    if not aspect_text:
                        aspect_text = "Аспект " + data["name"] + " между " + str(p1.get("name")) + " и " + str(p2.get("name"))

                    aspects_list.append({
                        "p1": p1.get("name"),
                        "p2": p2.get("name"),
                        "p1_key": p1_key,
                        "p2_key": p2_key,
                        "type": data["type"],
                        "name": data["name"],
                        "orb": round(abs(diff - angle), 2),
                        "exact_orb": round(diff, 2),
                        "text": aspect_text,
                    })

    return aspects_list


def find_cross_aspects(natal_planets, outer_planets, mode="transit", custom_orbs=None):
    # Кросс-аспекты: natal(строки) x outer(колонки) + текст из texts.db
    orbs = DEFAULT_ORBS.copy()
    if custom_orbs:
        orbs.update(custom_orbs)

    aspects_list = []

    for n in natal_planets:
        for o in outer_planets:
            diff = abs(n["abs_pos"] - o["abs_pos"])
            if diff > 180:
                diff = 360 - diff

            for angle, data in ASPECTS.items():
                orb = orbs.get(angle, data["orb"])
                if abs(diff - angle) <= orb:
                    n_key = n.get("key")
                    o_key = o.get("key")

                    aspect_text = get_db_aspect_text(n_key, o_key, data["type"], mode=mode, outer_planet=o_key, natal_planet=n_key)

                    aspects_list.append({
                        "p1": n.get("name"),
                        "p2": o.get("name"),
                        "p1_key": n_key,
                        "p2_key": o_key,
                        "type": data["type"],
                        "name": data["name"],
                        "orb": round(abs(diff - angle), 2),
                        "exact_orb": round(diff, 2),
                        "text": aspect_text or "",
                    })

    return aspects_list


def find_transit_aspects(natal_planets, transit_planets, custom_orbs=None):
    return find_cross_aspects(natal_planets, transit_planets, mode="transit", custom_orbs=custom_orbs)
