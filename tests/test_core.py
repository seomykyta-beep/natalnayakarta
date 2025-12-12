"""Тесты для core модулей"""
import pytest
import sys
sys.path.insert(0, '/opt/natal_chart')

from core.constants import ZODIAC_SIGNS, PLANET_NAMES
from core.texts import get_text, get_interpretation
from core.aspects import find_aspects, ASPECTS
from core.dignities import calculate_dignity


class TestConstants:
    def test_zodiac_signs_count(self):
        assert len(ZODIAC_SIGNS) == 12
    
    def test_planet_names_exist(self):
        assert 'sun' in PLANET_NAMES
        assert 'moon' in PLANET_NAMES


class TestDignities:
    def test_sun_in_leo_domicile(self):
        dignity, score = calculate_dignity('Sun', 'Лев')
        assert dignity == 'Обитель'
        assert score == 5
    
    def test_moon_in_cancer_domicile(self):
        dignity, score = calculate_dignity('Moon', 'Рак')
        assert dignity == 'Обитель'
        assert score == 5
    
    def test_no_dignity(self):
        dignity, score = calculate_dignity('Sun', 'Близнецы')
        assert dignity is None
        assert score == 0


class TestAspects:
    def test_aspects_defined(self):
        assert 0 in ASPECTS  # Соединение
        assert 180 in ASPECTS  # Оппозиция
        assert 120 in ASPECTS  # Тригон
    
    def test_find_aspects_empty(self):
        result = find_aspects([])
        assert result == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
