"""
Engine модуль - точка входа для всех расчётов.
Реэкспортирует функции из core/ для обратной совместимости.
"""
from core.constants import *
from core.texts import TEXTS, get_text, get_interpretation
from core.aspects import find_aspects, find_transit_aspects, ASPECTS, get_aspect_text_key
from core.houses import calculate_houses, calculate_placidus_houses, get_house_placement
from core.dignities import calculate_dignity, calculate_afetics, DIGNITIES
from core.calculator import (
    build_chart,
    calculate_real_chart,
    calculate_chart_with_mode,
    degrees_to_zodiac,
    get_city_info
)
from core.solar import find_solar_return
from core.lunar import find_lunar_return
from core.pdf import generate_pdf

__all__ = [
    'TEXTS', 'get_text', 'get_interpretation',
    'find_aspects', 'find_transit_aspects', 'ASPECTS',
    'calculate_houses', 'get_house_placement',
    'calculate_dignity', 'calculate_afetics', 'DIGNITIES',
    'build_chart', 'calculate_real_chart', 'calculate_chart_with_mode',
    'find_solar_return', 'find_lunar_return',
    'generate_pdf',
    'ZODIAC_SIGNS', 'PLANET_NAMES', 'PLANET_ICONS'
]
