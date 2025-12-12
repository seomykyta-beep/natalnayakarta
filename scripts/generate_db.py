import json

PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'North_node', 'South_node', 'Lilith']
SIGNS = ['Ari', 'Tau', 'Gem', 'Cnc', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
HOUSES = [str(i) for i in range(1, 13)]
ASPECTS = ['Conjunction', 'Sextile', 'Square', 'Trine', 'Opposition']

data = {
    "intro": "Здесь вводный текст для натальной карты...",
    "signs": {},
    "houses": {},
    "aspects": {}
}

# 1. Планеты в знаках
for p in PLANETS:
    data["signs"][p] = {}
    for s in SIGNS:
        data["signs"][p][s] = f"Описание: {p} в знаке {s} (ЗАПОЛНИТЬ)"

# 2. Планеты в домах
for p in PLANETS:
    data["houses"][p] = {}
    for h in HOUSES:
        data["houses"][p][h] = f"Описание: {p} в {h} доме (ЗАПОЛНИТЬ)"

# 3. Аспекты (каждая с каждой, без повторов)
for i in range(len(PLANETS)):
    for j in range(i + 1, len(PLANETS)):
        p1 = PLANETS[i]
        p2 = PLANETS[j]
        key = f"{p1}_{p2}"
        data["aspects"][key] = {}
        for a in ASPECTS:
            data["aspects"][key][a] = f"Описание: Аспект {a} между {p1} и {p2} (ЗАПОЛНИТЬ)"

# Сохраняем
with open("Натальная карта/texts.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("База знаний сгенерирована!")



