"""Расчёт солнечного возвращения (соляра)"""
from datetime import datetime, timedelta
import pytz


def find_solar_return(natal_sun_pos, target_year, latitude, longitude, tz_str, natal_month, natal_day):
    """Находит момент солнечного возвращения"""
    from .calculator import build_chart, ts, earth, planets
    
    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    
    # Начинаем поиск за день до дня рождения
    search_start = datetime(target_year, natal_month, natal_day, 0, 0)
    search_start = tz.localize(search_start) - timedelta(days=1)
    
    # Бинарный поиск точного момента
    step = timedelta(hours=12)
    current = search_start
    
    for _ in range(20):
        utc_dt = current.astimezone(pytz.UTC)
        t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
        
        sun = planets['sun']
        astrometric = earth.at(t).observe(sun)
        apparent = astrometric.apparent()
        _, lon_ecl, _ = apparent.ecliptic_latlon()
        current_sun_pos = lon_ecl.degrees % 360
        
        diff = (current_sun_pos - natal_sun_pos + 180) % 360 - 180
        
        if abs(diff) < 0.001:
            break
        
        if diff > 0:
            current -= step
        else:
            current += step
        
        step /= 2
    
    # Строим карту для момента соляра
    chart = build_chart(current, latitude, longitude, 'Solar Return')
    
    return {
        'datetime': current.strftime('%d.%m.%Y %H:%M'),
        'planets': chart['planets'],
        'houses': chart['houses'],
        'aspects': chart['aspects']
    }
