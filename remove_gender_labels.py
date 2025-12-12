#!/usr/bin/env python3
import json

with open('/opt/natal_chart/texts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

count = 0

# Убираем из SIGNS (Планеты в знаках)
for planet_key in data['signs']:
    for sign_key in data['signs'][planet_key]:
        text_dict = data['signs'][planet_key][sign_key]
        
        # Убираем "(Мужское выражение)" и "(Женское выражение)"
        if 'male' in text_dict and text_dict['male'].startswith('(Мужское выражение)'):
            # Берём только базовый текст без префикса
            base = text_dict.get('general', '')
            male_text = text_dict['male'].replace('(Мужское выражение) ', '').replace('\n\nДля мужчины эта позиция усиливает активное начало', '')
            data['signs'][planet_key][sign_key]['male'] = male_text.split('\n\nДля')[0].strip()
            count += 1
        
        if 'female' in text_dict and text_dict['female'].startswith('(Женское выражение)'):
            female_text = text_dict['female'].replace('(Женское выражение) ', '').replace('\n\nДля женщины эта позиция усиливает восприимчивость', '')
            data['signs'][planet_key][sign_key]['female'] = female_text.split('\n\nДля')[0].strip()
            count += 1

# Убираем из HOUSES (Планеты в домах)
for planet_key in data['houses']:
    for house_key in data['houses'][planet_key]:
        text_dict = data['houses'][planet_key][house_key]
        
        if 'male' in text_dict and '(Мужское выражение)' in text_dict['male']:
            male_text = text_dict['male'].replace('(Мужское выражение) ', '').split('\n\nДля мужчины')[0].strip()
            data['houses'][planet_key][house_key]['male'] = male_text
            count += 1
        
        if 'female' in text_dict and '(Женское выражение)' in text_dict['female']:
            female_text = text_dict['female'].replace('(Женское выражение) ', '').split('\n\nДля женщины')[0].strip()
            data['houses'][planet_key][house_key]['female'] = female_text
            count += 1

# Сохраняем
with open('/opt/natal_chart/texts.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Удалены гендерные обозначения из {count} текстов")
print("💾 Файл обновлён")
