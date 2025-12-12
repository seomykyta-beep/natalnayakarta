"""Работа с текстами интерпретаций"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def load_interpretation_texts():
    """Загружает тексты из JSON"""
    try:
        with open(BASE_DIR / 'data' / 'texts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'Error loading texts: {e}')
        return {}

TEXTS = load_interpretation_texts()


def get_text(category, key1, key2=None, gender='general'):
    """Получает текст интерпретации"""
    try:
        if key2:
            full_key = f'{key1}_{key2}'
        else:
            full_key = key1
        
        item = TEXTS.get(category, {}).get(full_key, {})
        
        if isinstance(item, dict):
            return item.get(gender, item.get('general', ''))
        return item if isinstance(item, str) else ''
    except:
        return ''


def get_interpretation(planet_key, sign, gender='general'):
    """Получает интерпретацию планеты в знаке"""
    key = f'{planet_key}_{sign}'
    
    data = TEXTS.get('signs', {}).get(key, {})
    if isinstance(data, dict):
        text = data.get(gender, data.get('general', ''))
    else:
        text = data if isinstance(data, str) else ''
    
    return text
