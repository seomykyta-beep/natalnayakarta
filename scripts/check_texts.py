#!/usr/bin/env python3
import json
import urllib.request

# Делаем запрос к API
url = "http://localhost:8000/api/calculate"
data = json.dumps({
    "name": "Test",
    "year": 1985,
    "month": 7,
    "day": 20,
    "hour": 14,
    "minute": 30,
    "city": "Moscow",
    "lat": 55.75,
    "lon": 37.62,
    "gender": "male"
}).encode()

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
response = urllib.request.urlopen(req)
result = json.loads(response.read())

# Проверяем текст
planets = result.get("planets", [])
print("✅ Проверка текстов в результатах расчёта:\n")
for i in range(min(3, len(planets))):
    p = planets[i]
    icon = p.get("icon", "")
    name = p.get("name", "")
    sign = p.get("sign", "")
    house = p.get("house", "")
    text = p.get("text", "НЕТ")
    
    print(f"{icon} {name} ({sign}, дом {house})")
    if text and text != "НЕТ":
        print(f"  ✓ Текст: {text[:150]}...\n")
    else:
        print(f"  ✗ БЕЗ ТЕКСТА\n")
