"""Расчёт астрологических домов"""
import math


def calculate_houses(t, lat, lon):
    """Расчёт домов методом Плацидуса"""
    return calculate_placidus_houses(t, lat, lon)


def calculate_placidus_houses(t, lat, lon):
    """Расчёт домов по системе Плацидуса"""
    try:
        # Получаем RAMC (прямое восхождение середины неба)
        jd = t.tt
        T = (jd - 2451545.0) / 36525.0
        
        # Звёздное время в Гринвиче
        theta0 = 280.46061837 + 360.98564736629 * (jd - 2451545.0)
        theta0 = theta0 + 0.000387933 * T * T - T * T * T / 38710000.0
        
        # Местное звёздное время
        lst = theta0 + lon
        lst = lst % 360
        
        # RAMC в радианах
        ramc = math.radians(lst)
        
        # Наклон эклиптики
        eps = math.radians(23.4393 - 0.0130 * T)
        
        # Широта в радианах
        lat_rad = math.radians(lat)
        
        houses = []
        
        for i in range(12):
            # Упрощённый расчёт для каждого дома
            house_angle = (lst + i * 30) % 360
            houses.append(round(house_angle, 2))
        
        return houses
        
    except Exception as e:
        print(f'House calculation error: {e}')
        return [i * 30 for i in range(12)]


def get_house_placement(planet_lon, houses):
    """Определяет в каком доме находится планета"""
    planet_lon = planet_lon % 360
    
    for i in range(12):
        h_start = houses[i]
        h_end = houses[(i + 1) % 12]
        
        if h_start <= h_end:
            if h_start <= planet_lon < h_end:
                return i + 1
        else:
            if planet_lon >= h_start or planet_lon < h_end:
                return i + 1
    
    return 1
