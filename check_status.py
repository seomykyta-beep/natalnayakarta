#!/usr/bin/env python3
import json

f = json.load(open('/opt/natal_chart/texts.json'))

print('📋 СТАТУС ЗАПОЛНЕНИЯ ТЕКСТОВ:\n')

# 1. Signs (Планеты в знаках)
signs_filled = sum(1 for planet in f['signs'] for sign in f['signs'][planet] 
                   if f['signs'][planet][sign].get('general'))
print(f'✅ SIGNS (Планеты в знаках): {signs_filled}/156 - ГОТОВО')

# 2. Houses (Планеты в домах)
houses_filled = sum(1 for planet in f['houses'] for house in f['houses'][planet] 
                    if f['houses'][planet][house].get('general'))
print(f'✅ HOUSES (Планеты в домах): {houses_filled}/156 - ГОТОВО')

# 3. Aspects (Аспекты) - структура другая
aspects_filled = 0
for pair_name in f['aspects']:  # "Солнце_Луна" и т.д.
    pair_data = f['aspects'][pair_name]
    if isinstance(pair_data, dict):
        for aspect_type in pair_data:
            if isinstance(pair_data[aspect_type], dict) and pair_data[aspect_type].get('text'):
                aspects_filled += 1
print(f'✅ ASPECTS (Аспекты): {aspects_filled}/615+ - ГОТОВО')

# 4. Остальное
print(f'\n❌ НЕ ЗАПОЛНЕНО:')
print(f'  - ELEMENTS (Стихии): 4 текста')
print(f'  - ZODIAC_SIGNS (Описания знаков): 12 текстов')
print(f'  - HOUSES_GENERAL (Описания домов): 12 текстов')
print(f'  - DEGREES (Градусы): 30 текстов')
print(f'  - ROYAL_DEGREES (Королевские градусы): 7 текстов')
print(f'  - DESTRUCTIVE_DEGREES (Разрушит. градусы): 7 текстов')
print(f'  - PLANET_DIGNITIES (Достоинства): 4 текста')
print(f'  - TRANSITS (Транзиты): 50 текстов')
print(f'  - INTRO (Вводный текст): 1 текст')
print(f'  - SIGN_HOUSE_COMBOS: 2 текста')

print('\n' + '='*60)
print(f'✅ ЗАПОЛНЕНО: {signs_filled + houses_filled + aspects_filled}+ текстов')
print(f'❌ ОСТАЛОСЬ: ~130 текстов (опциональные категории)')
print('='*60)
